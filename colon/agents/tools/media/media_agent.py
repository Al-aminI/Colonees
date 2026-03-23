# galos/agents/tools/media/media_agent.py
"""
Media Tool Agent

Thin integration layer — every capability is a tool the LLM calls autonomously.
No hidden orchestration, no manual prompts, no retry loops outside of tools.
Storage backend: local filesystem.
"""

import base64
import logging
import os
import random
import string
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from PIL import Image
from strands import Agent, tool

from galos.agents.tool_agents import BaseToolAgent
from galos.core.model_config import get_model

logger = logging.getLogger(__name__)

# Gemini model + endpoint (configurable via env)
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL_ID", "gemini-3-pro-image-preview")
GEMINI_IMAGE_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_IMAGE_MODEL}:generateContent"
)


class MediaToolAgent(BaseToolAgent):
    """
    Tool Agent for all media operations.

    Technology stack:
    - Script generation / refinement : Strands sub-agents
    - Text-to-speech narration       : Google Gemini TTS (REST)
    - Scene image generation         : Google Gemini (REST)
    - Image resizing / processing    : Pillow
    - Video assembly                 : ffmpeg
    - Artifact storage               : local filesystem
    """

    def __init__(self, *args, base_dir: Optional[str] = None, **kwargs):
        # Root directory for all media productions
        self.base_dir = Path(base_dir or os.getenv("COLONEES_MEDIA_DIR", "colonees_media")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.production_dir: Optional[Path] = None
        self.production_id: Optional[str] = None

        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_production(self) -> None:
        if not self.production_dir:
            raise RuntimeError("No active production. Call create_production first.")

    def _production_path(self, relative: str) -> Path:
        """Return an absolute path inside the active production directory."""
        self._require_production()
        p = (self.production_dir / relative).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # ------------------------------------------------------------------
    # Agent capabilities
    # ------------------------------------------------------------------

    def _create_agent(self) -> Agent:
        return Agent(
            name=self.agent_id,
            system_prompt="Media tool provider - not used standalone",
            model=get_model(),
            session_manager=self.session_manager,
            tools=[],
        )

    def get_capabilities(self) -> List[str]:
        return [
            "script_generation", "text_to_speech", "image_generation",
            "image_processing", "video_assembly", "local_storage",
        ]

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    @tool
    def create_production(self, production_name: str) -> Dict[str, Any]:
        """
        Create a dedicated local directory for this production and activate it
        as the current production context. Must be called before any other tool.

        Args:
            production_name: Human-readable name for the production.
        """
        try:
            slug = "".join(c if c.isalnum() else "-" for c in production_name.lower()).strip("-")[:40]
            production_id = str(uuid.uuid4())
            prod_dir = self.base_dir / f"prod-{slug}-{production_id[:8]}"
            for sub in ("images", "narration", "video", "scripts", "state"):
                (prod_dir / sub).mkdir(parents=True, exist_ok=True)

            self.production_id = production_id
            self.production_dir = prod_dir
            logger.info("Production directory ready: %s", prod_dir)
            return {
                "status": "success",
                "production_dir": str(prod_dir),
                "production_id": production_id,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    # Keep old name as alias so existing specialist system prompts still work
    @tool
    def create_production_bucket(self, production_name: str) -> Dict[str, Any]:
        """Alias for create_production (backward compatibility)."""
        return self.create_production(production_name)

    @tool
    async def write_script(self, instructions: str) -> Dict[str, Any]:
        """
        Use an AI sub-agent to write or refine a scene-by-scene video script.

        Args:
            instructions: Full natural-language brief — topic, target duration, audience,
                          style, tone, any refinement notes. Be as specific as needed.
        """
        try:
            agent = Agent(
                system_prompt="""You are an expert video scriptwriter for professional productions.
Write clear, engaging scripts suitable for any domain or audience.
Return ONLY valid JSON:
{
  "title": "...",
  "total_duration_seconds": N,
  "scenes": [
    {
      "scene_number": 1,
      "narration": "...",
      "on_screen_text": ["..."],
      "duration_seconds": N
    }
  ]
}

CRITICAL REQUIREMENTS FOR MAXIMUM SCENES:
- CREATE AS MANY SCENES AS POSSIBLE (minimum 10-15 scenes for a 2-minute video)
- Each scene should be 8-12 seconds long (short and focused)
- Break the topic into MANY small, focused points
- Each scene = ONE concept = ONE short narration (1-3 sentences max)
- More scenes = better engagement and pacing
- DO NOT create long narrations - keep them SHORT and SPECIFIC

NARRATION REQUIREMENTS:
- Each scene must have a scene_number field (1, 2, 3, ... N)
- Each scene must have a narration field with SHORT text (1-3 sentences)
- DO NOT include visual_suggestion field - images will be generated from narration
- The narration text will be used for BOTH audio synthesis AND image generation
- Make narration DESCRIPTIVE and VISUAL so it can be illustrated
- Narration should describe what the viewer should SEE and UNDERSTAND

REMEMBER: SHORT narrations, MANY scenes, VISUAL descriptions!""",
                model=get_model(),
            )
            response = agent(instructions)
            script_text = response.message if hasattr(response, "message") else str(response)
            return {"status": "success", "script": script_text}
        except Exception as e:
            logger.error("write_script failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def sanitize_image_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Clean a visual description so it is safe to send to Gemini Imagen.
        Removes real people's names, photography references, and other phrases
        known to trigger safety filters.

        Always call this before generate_image.

        Args:
            prompt: Raw visual description from the script.
        """
        import re

        replacements = [
            (
                r"\b(Andrew Ng|Elon Musk|Bill Gates|Jeff Bezos|Mark Zuckerberg|"
                r"Satya Nadella|Tim Cook|Steve Jobs|Warren Buffett|Sundar Pichai|Jensen Huang)\b",
                "a professional",
            ),
            (
                r"\b(photo of|photograph of|picture of|image of|realistic photo)\b",
                "professional illustration of",
            ),
            (r"\b(real person|celebrity|famous person|well-known figure)\b", "professional"),
        ]

        cleaned = prompt
        changes = []
        for pattern, replacement in replacements:
            new, n = re.subn(pattern, replacement, cleaned, flags=re.IGNORECASE)
            if n:
                changes.append(f"replaced {n}x: '{pattern}' → '{replacement}'")
            cleaned = new

        return {
            "status": "success",
            "original_prompt": prompt,
            "sanitized_prompt": cleaned,
            "changes_made": changes,
        }

    @tool
    def generate_image(
        self,
        prompt: str,
        course: str = "",
        max_retries: int = 3,
        scene_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a scene image via the Gemini REST API and save the PNG to the
        active production directory. Retries automatically on overload/rate-limit.

        Always call sanitize_image_prompt first.

        Args:
            prompt:      Sanitized visual description for the scene.
            course:      Topic name (used in fallback prompt).
            max_retries: Number of attempts before giving up (default 3).
            scene_number: Optional scene number for tracking.
        """
        try:
            self._require_production()

            headers = {
                "x-goog-api-key": self._gemini_api_key,
                "Content-Type": "application/json",
            }

            def _build_payload(p: str) -> Dict:
                return {
                    "contents": [{"parts": [{"text": p}]}],
                    "generationConfig": {"responseModalities": ["IMAGE"]},
                }

            last_error: Optional[str] = None

            for attempt in range(max_retries):
                current_prompt = (
                    prompt
                    if attempt == 0
                    else f"Professional illustration: {course or prompt[:80]}. "
                    "Clean modern flat design, 16:9 widescreen format."
                )

                try:
                    resp = requests.post(
                        GEMINI_IMAGE_URL,
                        headers=headers,
                        json=_build_payload(current_prompt),
                        timeout=120,
                    )
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    time.sleep((attempt + 1) * 2)
                    continue

                if resp.status_code == 503:
                    time.sleep((attempt + 1) * 5)
                    continue
                if resp.status_code == 429:
                    time.sleep((attempt + 1) * 3)
                    continue

                resp.raise_for_status()
                data = resp.json()

                image_bytes: Optional[bytes] = None
                for candidate in data.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            image_bytes = base64.b64decode(part["inlineData"]["data"])
                            break
                    if image_bytes:
                        break

                if image_bytes:
                    name = "".join(random.choices(string.ascii_letters + string.digits, k=14))
                    file_path = self._production_path(f"images/raw_{name}.png")
                    file_path.write_bytes(image_bytes)
                    local_uri = str(file_path)
                    logger.info("Image saved -> %s", local_uri)
                    result = {"status": "success", "local_path": local_uri, "attempt": attempt + 1}
                    if scene_number is not None:
                        result["scene_number"] = scene_number
                    return result

                finish_reason = (
                    data.get("candidates", [{}])[0].get("finishReason", "UNKNOWN")
                    if data.get("candidates")
                    else "NO_CANDIDATES"
                )
                last_error = f"No image returned. finishReason={finish_reason}"
                logger.warning("Attempt %d/%d: %s", attempt + 1, max_retries, last_error)

                if finish_reason in ("SAFETY", "RECITATION", "NO_IMAGE") and attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                break

            return {"status": "failed", "error": last_error or "Unknown error after all retries"}

        except RuntimeError as e:
            logger.error("generate_image failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def resize_image(
        self,
        local_path: str,
        width: int = 1280,
        height: int = 720,
        scene_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Load an image from disk, resize and center-crop it to the exact target
        dimensions, then save the result back to the production directory.

        Always call this after generate_image before passing images to assemble_video.
        Default target is 1280x720 (16:9) for video compatibility.

        Args:
            local_path: Local filesystem path of the source image (from generate_image).
            width:      Target width in pixels.
            height:     Target height in pixels.
            scene_number: Optional scene number for tracking.
        """
        try:
            self._require_production()

            raw = Path(local_path).read_bytes()
            img = Image.open(BytesIO(raw)).convert("RGB")

            img_ratio = img.width / img.height
            target_ratio = width / height

            if img_ratio > target_ratio:
                new_h, new_w = height, int(height * img_ratio)
            else:
                new_w, new_h = width, int(width / img_ratio)

            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            img = img.crop((left, top, left + width, top + height))

            buf = BytesIO()
            img.save(buf, format="PNG", optimize=True)

            name = "".join(random.choices(string.ascii_letters + string.digits, k=14))
            out_path = self._production_path(f"images/resized_{name}.png")
            out_path.write_bytes(buf.getvalue())

            logger.info("Resized image (%dx%d) -> %s", width, height, out_path)
            result = {
                "status": "success",
                "local_path": str(out_path),
                "width": width,
                "height": height,
            }
            if scene_number is not None:
                result["scene_number"] = scene_number
            return result

        except RuntimeError as e:
            logger.error("resize_image failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def text_to_speech(
        self,
        text: str,
        locale: str = "en-US",
        voice_gender: str = "female",
        voice_id: Optional[str] = None,
        engine: str = "gemini",
        scene_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Convert narration text to speech using Google Gemini TTS and save the
        MP3 to the active production directory.

        Args:
            text:         Narration text for one scene (max 5000 chars).
            locale:       BCP-47 locale code e.g. 'en-US', 'en-GB', 'fr-FR'.
            voice_gender: 'female' (default) or 'male'.
            voice_id:     Override: explicit voice name, skips locale/gender lookup.
            engine:       Kept for API compatibility — always uses Gemini TTS.
            scene_number: Optional scene number for tracking.
        """
        try:
            self._require_production()

            if not text or not text.strip():
                return {"status": "failed", "error": "Text cannot be empty"}

            if len(text) > 5000:
                return {
                    "status": "failed",
                    "error": f"Text is {len(text)} characters — exceeds 5000-character limit. "
                    "Split the narration into shorter chunks.",
                }

            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self._gemini_api_key}"

            voice_name_map = {
                "en-US": {"female": "en-US-Neural2-F", "male": "en-US-Neural2-D"},
                "en-GB": {"female": "en-GB-Neural2-A", "male": "en-GB-Neural2-B"},
                "en-AU": {"female": "en-AU-Neural2-A", "male": "en-AU-Neural2-B"},
                "en-IN": {"female": "en-IN-Neural2-A", "male": "en-IN-Neural2-B"},
                "en-NG": {"female": "en-GB-Neural2-A", "male": "en-GB-Neural2-B"},
                "es-US": {"female": "es-US-Neural2-A", "male": "es-US-Neural2-B"},
                "es-ES": {"female": "es-ES-Neural2-A", "male": "es-ES-Neural2-B"},
                "fr-FR": {"female": "fr-FR-Neural2-A", "male": "fr-FR-Neural2-B"},
                "de-DE": {"female": "de-DE-Neural2-A", "male": "de-DE-Neural2-B"},
                "it-IT": {"female": "it-IT-Neural2-A", "male": "it-IT-Neural2-C"},
                "pt-BR": {"female": "pt-BR-Neural2-A", "male": "pt-BR-Neural2-B"},
                "ja-JP": {"female": "ja-JP-Neural2-B", "male": "ja-JP-Neural2-C"},
                "ko-KR": {"female": "ko-KR-Neural2-A", "male": "ko-KR-Neural2-C"},
                "zh-CN": {"female": "cmn-CN-Neural2-A", "male": "cmn-CN-Neural2-B"},
            }

            resolved_voice = (
                voice_id
                or voice_name_map.get(locale, {}).get(voice_gender)
                or "en-US-Neural2-F"
            )
            api_locale = "en-GB" if locale == "en-NG" else locale

            payload = {
                "input": {"text": text},
                "voice": {"languageCode": api_locale, "name": resolved_voice},
                "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0, "pitch": 0.0},
            }

            response = requests.post(url, json=payload, timeout=60)
            if response.status_code != 200:
                return {
                    "status": "failed",
                    "error": f"Gemini TTS error: {response.status_code} - {response.text[:200]}",
                }

            audio_content = response.json().get("audioContent")
            if not audio_content:
                return {"status": "failed", "error": "No audio content in Gemini response"}

            audio_bytes = base64.b64decode(audio_content)
            out_path = self._production_path(f"narration/{uuid.uuid4()}.mp3")
            out_path.write_bytes(audio_bytes)

            actual_duration = self._get_audio_duration(audio_bytes)
            logger.info("TTS saved -> %s (voice=%s, locale=%s, duration=%.2fs)", out_path, resolved_voice, locale, actual_duration)

            result = {
                "status": "success",
                "local_path": str(out_path),
                "voice_id": resolved_voice,
                "locale": locale,
                "engine": "gemini",
                "character_count": len(text),
                "duration_seconds": actual_duration,
            }
            if scene_number is not None:
                result["scene_number"] = scene_number
            return result

        except RuntimeError as e:
            logger.error("text_to_speech failed: %s", e)
            return {"status": "failed", "error": str(e)}

    def _get_audio_duration(self, audio_bytes: bytes) -> float:
        """Get the actual duration of an audio file in seconds using ffprobe."""
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    tmp_path,
                ],
                capture_output=True, text=True, check=True, timeout=10,
            )
            return float(result.stdout.strip())
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    @tool
    def assemble_video(
        self,
        scene_image_paths: List[str],
        audio_paths: List[str],
        fps: int = 24,
        resolution: str = "1280x720",
    ) -> Dict[str, Any]:
        """
        Pair each scene image with its audio track and concatenate them into a
        single MP4 using ffmpeg, then save it to the production directory.

        Images should already be resized (call resize_image first).

        Args:
            scene_image_paths: Ordered local paths for scene PNG images.
            audio_paths:       Ordered local paths for scene MP3 narrations (same length).
            fps:               Output frames per second (default 24).
            resolution:        Output resolution as 'WxH' (default '1280x720').
        """
        import subprocess

        try:
            self._require_production()
            n = len(scene_image_paths)
            w, h = resolution.split("x")

            # Measure exact audio durations
            durations = []
            for aud_path in audio_paths:
                probe = subprocess.run(
                    [
                        "ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        aud_path,
                    ],
                    capture_output=True, text=True, check=True,
                )
                durations.append(float(probe.stdout.strip()))

            cmd = ["ffmpeg", "-y"]
            for img, dur in zip(scene_image_paths, durations):
                cmd += ["-loop", "1", "-framerate", str(fps), "-t", str(dur), "-i", img]
            for aud in audio_paths:
                cmd += ["-i", aud]

            filter_parts = []
            for i in range(n):
                filter_parts.append(
                    f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
                    f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                    f"setsar=1,fps={fps}[v{i}]"
                )
                filter_parts.append(f"[{n + i}:a]asetpts=PTS-STARTPTS[a{i}]")

            concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(n))
            filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=1[outv][outa]")

            output_path = self._production_path(f"video/{uuid.uuid4()}.mp4")
            cmd += [
                "-filter_complex", ";".join(filter_parts),
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-c:a", "aac",
                "-preset", "fast", "-crf", "23",
                "-movflags", "+faststart",
                str(output_path),
            ]

            logger.info("Assembling %d scenes...", n)
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                err = result.stderr.decode() if isinstance(result.stderr, bytes) else str(result.stderr)
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

            size_mb = round(output_path.stat().st_size / (1024 * 1024), 2)
            logger.info("Video assembled -> %s (%.2fMB)", output_path, size_mb)
            return {
                "status": "success",
                "local_path": str(output_path),
                "scenes": n,
                "size_mb": size_mb,
            }

        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            logger.error("assemble_video ffmpeg error: %s", err)
            return {"status": "failed", "error": err}
        except RuntimeError as e:
            logger.error("assemble_video failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def save_to_disk(self, key: str, content: str) -> Dict[str, Any]:
        """
        Persist any text content (script JSON, path lists, state notes) to the
        active production directory.

        Args:
            key:     Relative path e.g. 'scripts/draft.json' or 'state/image_paths.json'.
            content: Text content to store.
        """
        try:
            out_path = self._production_path(key)
            out_path.write_text(content, encoding="utf-8")
            return {"status": "success", "local_path": str(out_path)}
        except RuntimeError as e:
            return {"status": "failed", "error": str(e)}

    # Backward-compat alias used by specialist system prompts
    @tool
    def save_to_s3(self, key: str, content: str) -> Dict[str, Any]:
        """Alias for save_to_disk (backward compatibility)."""
        return self.save_to_disk(key, content)

    @tool
    def load_from_disk(self, key: str) -> str:
        """
        Retrieve previously saved text content from the active production directory.

        Args:
            key: The relative path used when the content was saved.

        Returns:
            String containing the content. On error, returns "ERROR loading <key>: <message>".
        """
        try:
            out_path = self._production_path(key)
            return out_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"ERROR loading {key}: {str(e)}"

    # Backward-compat alias
    @tool
    def load_from_s3(self, key: str) -> str:
        """Alias for load_from_disk (backward compatibility)."""
        return self.load_from_disk(key)

    @tool
    def list_artifacts(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List all artifacts stored in the active production directory, grouped by category.

        Categories: scripts/, narration/, images/, video/, state/

        Args:
            category: Optional subfolder to filter by e.g. 'images' or 'narration'.
        """
        try:
            self._require_production()
            search_root = self.production_dir / category if category else self.production_dir
            artifacts: Dict[str, List[Dict]] = {}
            total_size = 0

            for abs_path in sorted(search_root.rglob("*")):
                if not abs_path.is_file():
                    continue
                rel = abs_path.relative_to(self.production_dir)
                parts = rel.parts
                cat = parts[0] if len(parts) > 1 else "root"
                size = abs_path.stat().st_size
                total_size += size
                artifacts.setdefault(cat, []).append({
                    "local_path": str(abs_path),
                    "size_bytes": size,
                })

            return {
                "status": "success",
                "production_id": self.production_id,
                "production_dir": str(self.production_dir),
                "artifacts_by_category": artifacts,
                "total_artifacts": sum(len(v) for v in artifacts.values()),
                "total_size_bytes": total_size,
            }
        except RuntimeError as e:
            logger.error("list_artifacts failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def delete_artifact(self, local_path: str) -> Dict[str, Any]:
        """
        Delete a specific artifact from the active production directory.

        Args:
            local_path: Absolute local path of the artifact to delete.
        """
        try:
            self._require_production()
            p = Path(local_path)
            if p.exists():
                p.unlink()
            logger.info("Deleted artifact: %s", local_path)
            return {"status": "success", "deleted_path": local_path}
        except Exception as e:
            logger.error("delete_artifact failed: %s", e)
            return {"status": "failed", "error": str(e)}

    @tool
    def get_production_info(self) -> Dict[str, Any]:
        """
        Return a summary of the current production context: directory, production ID,
        and a count of artifacts in each category.
        """
        try:
            self._require_production()
            manifest = self.list_artifacts()
            if manifest["status"] == "failed":
                return manifest
            return {
                "status": "success",
                "production_id": self.production_id,
                "production_dir": str(self.production_dir),
                "artifact_summary": {
                    cat: len(items)
                    for cat, items in manifest["artifacts_by_category"].items()
                },
                "total_artifacts": manifest["total_artifacts"],
                "total_size_bytes": manifest["total_size_bytes"],
            }
        except RuntimeError as e:
            logger.error("get_production_info failed: %s", e)
            return {"status": "failed", "error": str(e)}
