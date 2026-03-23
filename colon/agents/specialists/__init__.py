"""
Colonees Specialist Agents

All specialist agents organized by domain.
"""

from galos.agents.specialists.tutoring.specialist import TutorSpecialistAgent
from galos.agents.specialists.subject_expertise.specialist import SubjectExpertSpecialistAgent
from galos.agents.specialists.research.specialist import ResearchSpecialistAgent
from galos.agents.specialists.assessment.specialist import AssessmentSpecialistAgent
from galos.agents.specialists.video_production.specialist import VideoProductionSpecialistAgent

__all__ = [
    'TutorSpecialistAgent',
    'SubjectExpertSpecialistAgent',
    'ResearchSpecialistAgent',
    'AssessmentSpecialistAgent',
    'VideoProductionSpecialistAgent',
]
