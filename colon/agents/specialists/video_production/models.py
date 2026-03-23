"""
Data models for video generation specialists.

This module defines the core data structures used in the video production pipeline,
including VideoStructure, Scene, AudioCue, VideoAsset, ProductionState, and VideoStyle.
All models include validation rules to ensure data integrity throughout the pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AssetType(Enum):
    """Types of video assets that can be generated."""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ANIMATION = "animation"
    TRANSITION = "transition"
    TEXT_OVERLAY = "text_overlay"


class AssetStatus(Enum):
    """Status of asset generation."""
    QUEUED = "queued"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    RETRYING = "retrying"


class ProductionStage(Enum):
    """Stages in the video production pipeline."""
    PLANNING = "planning"
    SCRIPT_GENERATION = "script_generation"
    AUDIO_GENERATION = "audio_generation"
    VISUAL_GENERATION = "visual_generation"
    ASSEMBLY = "assembly"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AudioCue:
    """
    Represents an audio cue within a scene.
    
    Attributes:
        cue_type: Type of audio ('narration', 'music', 'sound_effect')
        start_time: Start time in seconds relative to scene start
        duration: Duration in seconds
        content: Text content for narration or description for other types
        parameters: Additional parameters for audio generation
    """
    cue_type: str
    start_time: float
    duration: float
    content: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate audio cue data."""
        if self.cue_type not in ['narration', 'music', 'sound_effect']:
            raise ValueError(
                f"Invalid cue_type '{self.cue_type}'. "
                f"Must be one of: 'narration', 'music', 'sound_effect'"
            )
        
        if self.start_time < 0:
            raise ValueError(f"start_time must be non-negative, got {self.start_time}")
        
        if self.duration <= 0:
            raise ValueError(f"duration must be positive, got {self.duration}")
        
        if not self.content or not self.content.strip():
            raise ValueError("content must be non-empty")


@dataclass
class Scene:
    """
    Represents a single scene in a video.
    
    Attributes:
        scene_id: Unique identifier for the scene
        sequence_number: Position in the video (starting from 1)
        duration: Duration in seconds
        description: Visual description of the scene
        narration_text: Text to be narrated in this scene
        visual_style: Style for visual generation
        transition_in: Type of transition entering this scene
        transition_out: Type of transition exiting this scene
        audio_cues: List of audio cues for this scene
    
    Validation:
        - sequence_number must be positive
        - duration must be positive
        - description must be non-empty
        - narration_text must be non-empty
    """
    scene_id: str
    sequence_number: int
    duration: float
    description: str
    narration_text: str
    visual_style: str
    transition_in: str
    transition_out: str
    audio_cues: List[AudioCue] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate scene data."""
        if self.sequence_number < 1:
            raise ValueError(
                f"sequence_number must be >= 1, got {self.sequence_number}"
            )
        
        if self.duration <= 0:
            raise ValueError(f"duration must be positive, got {self.duration}")
        
        if not self.description or not self.description.strip():
            raise ValueError("description must be non-empty")
        
        if not self.narration_text or not self.narration_text.strip():
            raise ValueError("narration_text must be non-empty")


@dataclass
class VideoStyle:
    """
    Configuration for video style and aesthetics.
    
    Attributes:
        style_name: Name of the style preset
        visual_style: Visual rendering style
        color_palette: List of hex color codes
        font_family: Font family for text overlays
        animation_intensity: Animation intensity (0.0 to 1.0)
        transition_style: Style of transitions between scenes
        music_genre: Genre for background music
        narration_voice: Voice type for narration
        pacing: Video pacing ('slow', 'moderate', 'fast')
    
    Validation:
        - color_palette must contain valid hex codes
        - animation_intensity must be between 0.0 and 1.0
        - pacing must be one of: 'slow', 'moderate', 'fast'
    """
    style_name: str
    visual_style: str
    color_palette: List[str]
    font_family: str
    animation_intensity: float
    transition_style: str
    music_genre: str
    narration_voice: str
    pacing: str
    
    def __post_init__(self):
        """Validate video style data."""
        # Validate color palette
        for color in self.color_palette:
            if not self._is_valid_hex_color(color):
                raise ValueError(
                    f"Invalid hex color code '{color}'. "
                    f"Must be in format #RRGGBB or #RGB"
                )
        
        # Validate animation intensity
        if not 0.0 <= self.animation_intensity <= 1.0:
            raise ValueError(
                f"animation_intensity must be between 0.0 and 1.0, "
                f"got {self.animation_intensity}"
            )
        
        # Validate pacing
        valid_pacing = ['slow', 'moderate', 'fast']
        if self.pacing not in valid_pacing:
            raise ValueError(
                f"pacing must be one of {valid_pacing}, got '{self.pacing}'"
            )
    
    @staticmethod
    def _is_valid_hex_color(color: str) -> bool:
        """Check if a string is a valid hex color code."""
        if not color.startswith('#'):
            return False
        
        hex_part = color[1:]
        if len(hex_part) not in [3, 6]:
            return False
        
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False


@dataclass
class VideoStructure:
    """
    Represents the planned structure of a video.
    
    Attributes:
        video_id: Unique identifier for the video
        topic: Topic or subject of the video
        style: Video style configuration
        duration: Target duration in seconds
        target_audience: Intended audience for the video
        scenes: List of scenes in the video
        metadata: Additional metadata
        created_at: Timestamp of creation
    
    Validation:
        - scenes must have consecutive sequence numbers starting from 1
        - total scene durations must match target duration (±5%)
        - all scenes must have non-empty descriptions and narration
    """
    video_id: str
    topic: str
    style: VideoStyle
    duration: int
    target_audience: str
    scenes: List[Scene]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate video structure data."""
        # Validate scene sequence numbers
        self._validate_scene_sequence()
        
        # Validate total duration
        self._validate_total_duration()
        
        # Validate scene content
        self._validate_scene_content()
    
    def _validate_scene_sequence(self):
        """Validate that scene sequence numbers are consecutive starting from 1."""
        if not self.scenes:
            raise ValueError("scenes list cannot be empty")
        
        # Sort scenes by sequence number for validation
        sorted_scenes = sorted(self.scenes, key=lambda s: s.sequence_number)
        
        for i, scene in enumerate(sorted_scenes):
            expected_sequence = i + 1
            if scene.sequence_number != expected_sequence:
                raise ValueError(
                    f"Scene sequence numbers must be consecutive starting from 1. "
                    f"Expected sequence_number {expected_sequence}, "
                    f"got {scene.sequence_number} for scene {scene.scene_id}"
                )
    
    def _validate_total_duration(self):
        """Validate that total scene durations match target duration (±5%)."""
        total_scene_duration = sum(scene.duration for scene in self.scenes)
        tolerance = 0.05 * self.duration
        
        if abs(total_scene_duration - self.duration) > tolerance:
            raise ValueError(
                f"Total scene durations ({total_scene_duration}s) must match "
                f"target duration ({self.duration}s) within 5% tolerance "
                f"(±{tolerance}s). Difference: "
                f"{abs(total_scene_duration - self.duration)}s"
            )
    
    def _validate_scene_content(self):
        """Validate that all scenes have non-empty descriptions and narration."""
        for scene in self.scenes:
            if not scene.description or not scene.description.strip():
                raise ValueError(
                    f"Scene {scene.scene_id} has empty description"
                )
            
            if not scene.narration_text or not scene.narration_text.strip():
                raise ValueError(
                    f"Scene {scene.scene_id} has empty narration_text"
                )


@dataclass
class VideoAsset:
    """
    Represents a generated video asset.
    
    Attributes:
        asset_id: Unique identifier for the asset
        asset_type: Type of asset (image, audio, video, etc.)
        scene_id: ID of the scene this asset belongs to
        file_path: Path to the asset file
        file_format: Format of the file (mp4, png, wav, etc.)
        file_size: Size of the file in bytes
        duration: Duration in seconds (for time-based assets)
        resolution: Resolution tuple (width, height) for visual assets
        metadata: Additional metadata
        created_at: Timestamp of creation
        status: Current status of the asset
    
    Validation:
        - Assets with READY status must have non-empty file paths
    """
    asset_id: str
    asset_type: AssetType
    scene_id: str
    file_path: str
    file_format: str
    file_size: int
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: AssetStatus = AssetStatus.QUEUED
    
    def __post_init__(self):
        """Validate video asset data."""
        # Validate that READY assets have valid file paths
        if self.status == AssetStatus.READY:
            if not self.file_path or not self.file_path.strip():
                raise ValueError(
                    f"Asset {self.asset_id} has status READY but empty file_path"
                )
        
        # Validate file size is non-negative
        if self.file_size < 0:
            raise ValueError(
                f"file_size must be non-negative, got {self.file_size}"
            )
        
        # Validate duration if present
        if self.duration is not None and self.duration < 0:
            raise ValueError(
                f"duration must be non-negative, got {self.duration}"
            )
        
        # Validate resolution if present
        if self.resolution is not None:
            width, height = self.resolution
            if width <= 0 or height <= 0:
                raise ValueError(
                    f"resolution dimensions must be positive, got {self.resolution}"
                )


@dataclass
class ProductionState:
    """
    Tracks the current state of video production.
    
    Attributes:
        video_id: Unique identifier for the video
        current_stage: Current production stage
        script: Generated script data
        audio_assets: List of generated audio assets
        visual_assets: List of generated visual assets
        final_video: Final assembled video asset
        progress_percentage: Progress from 0.0 to 100.0
        errors: List of error messages
        started_at: Timestamp when production started
        completed_at: Timestamp when production completed
    
    Validation:
        - progress_percentage must be between 0.0 and 100.0
        - stage transitions must follow sequential order
    """
    video_id: str
    current_stage: ProductionStage
    script: Optional[Dict[str, Any]] = None
    audio_assets: List[VideoAsset] = field(default_factory=list)
    visual_assets: List[VideoAsset] = field(default_factory=list)
    final_video: Optional[VideoAsset] = None
    progress_percentage: float = 0.0
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate production state data."""
        # Validate progress percentage
        if not 0.0 <= self.progress_percentage <= 100.0:
            raise ValueError(
                f"progress_percentage must be between 0.0 and 100.0, "
                f"got {self.progress_percentage}"
            )
    
    def update_stage(self, new_stage: ProductionStage):
        """
        Update the production stage with validation.
        
        Args:
            new_stage: The new production stage
        
        Raises:
            ValueError: If stage transition is invalid (regression)
        """
        stage_order = [
            ProductionStage.PLANNING,
            ProductionStage.SCRIPT_GENERATION,
            ProductionStage.AUDIO_GENERATION,
            ProductionStage.VISUAL_GENERATION,
            ProductionStage.ASSEMBLY,
            ProductionStage.POST_PROCESSING,
            ProductionStage.COMPLETED,
        ]
        
        # Allow transition to FAILED from any stage
        if new_stage == ProductionStage.FAILED:
            self.current_stage = new_stage
            return
        
        # Check for valid progression
        try:
            current_index = stage_order.index(self.current_stage)
            new_index = stage_order.index(new_stage)
            
            if new_index < current_index:
                raise ValueError(
                    f"Invalid stage transition: cannot regress from "
                    f"{self.current_stage.value} to {new_stage.value}"
                )
            
            self.current_stage = new_stage
        except ValueError as e:
            if "is not in list" in str(e):
                raise ValueError(f"Invalid production stage: {new_stage}")
            raise
