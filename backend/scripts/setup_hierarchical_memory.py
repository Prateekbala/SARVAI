"""
Initial setup script for hierarchical memory system
Run this after database migration to initialize the system
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import get_db, init_db
from app.models.models import Memory, User
from app.services.memory.memory_manager import memory_manager
from sqlalchemy import select, func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def classify_existing_memories():
    """Classify all existing memories into episodic/semantic"""
    
    logger.info("Starting memory classification...")
    
    async for db in get_db():
        try:
            # Get all memories without classification
            result = await db.execute(
                select(Memory).where(
                    (Memory.memory_type == None) | (Memory.memory_type == 'episodic')
                )
            )
            memories = result.scalars().all()
            
            logger.info(f"Found {len(memories)} memories to classify")
            
            classified = {"episodic": 0, "semantic": 0, "procedural": 0}
            
            for memory in memories:
                try:
                    memory_type = await memory_manager.classify_memory(db, memory)
                    memory.memory_type = memory_type
                    classified[memory_type] = classified.get(memory_type, 0) + 1
                    
                    if classified[memory_type] % 10 == 0:
                        logger.info(f"Classified {sum(classified.values())} memories...")
                        
                except Exception as e:
                    logger.error(f"Failed to classify memory {memory.id}: {e}")
                    continue
            
            await db.commit()
            logger.info(f"Classification complete: {classified}")
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            await db.rollback()
            raise


async def calculate_initial_importance():
    """Calculate importance scores for existing memories"""
    
    logger.info("Calculating initial importance scores...")
    
    async for db in get_db():
        try:
            result = await db.execute(
                select(Memory).where(
                    (Memory.importance_score == None) | (Memory.importance_score == 50)
                )
            )
            memories = result.scalars().all()
            
            logger.info(f"Calculating importance for {len(memories)} memories")
            
            for i, memory in enumerate(memories):
                try:
                    importance = await memory_manager.get_memory_importance(db, memory.id)
                    memory.importance_score = int(importance * 100)  # Convert to 0-100 scale
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(memories)} memories...")
                        
                except Exception as e:
                    logger.error(f"Failed to calculate importance for {memory.id}: {e}")
                    memory.importance_score = 50  # Default
                    continue
            
            await db.commit()
            logger.info("Importance calculation complete")
            
        except Exception as e:
            logger.error(f"Importance calculation failed: {e}")
            await db.rollback()
            raise


async def run_initial_consolidation():
    """Run initial consolidation for all users"""
    
    logger.info("Running initial memory consolidation...")
    
    async for db in get_db():
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            logger.info(f"Consolidating memories for {len(users)} users")
            
            total_consolidated = 0
            total_summaries = 0
            
            for user in users:
                try:
                    result = await memory_manager.consolidate_memories(
                        db=db,
                        user_id=user.id,
                        force=False
                    )
                    
                    total_consolidated += result["consolidated"]
                    total_summaries += result["summaries_created"]
                    
                    logger.info(
                        f"User {user.email}: "
                        f"{result['consolidated']} memories -> "
                        f"{result['summaries_created']} summaries"
                    )
                    
                except Exception as e:
                    logger.error(f"Consolidation failed for user {user.id}: {e}")
                    continue
            
            logger.info(
                f"Consolidation complete: "
                f"{total_consolidated} memories consolidated into "
                f"{total_summaries} summaries"
            )
            
        except Exception as e:
            logger.error(f"Consolidation failed: {e}")
            raise


async def verify_setup():
    """Verify the setup is working correctly"""
    
    logger.info("Verifying setup...")
    
    async for db in get_db():
        try:
            # Check classified memories
            result = await db.execute(
                select(Memory.memory_type, func.count(Memory.id)).
                group_by(Memory.memory_type)
            )
            
            memory_types = dict(result.all())
            logger.info(f"Memory types: {memory_types}")
            
            # Check importance scores
            result = await db.execute(
                select(
                    func.avg(Memory.importance_score).label("avg"),
                    func.min(Memory.importance_score).label("min"),
                    func.max(Memory.importance_score).label("max")
                )
            )
            
            stats = result.first()
            logger.info(
                f"Importance scores - "
                f"avg: {stats.avg:.2f}, "
                f"min: {stats.min}, "
                f"max: {stats.max}"
            )
            
            # Check summaries
            from app.models.models import MemorySummary
            result = await db.execute(
                select(func.count(MemorySummary.id))
            )
            
            summary_count = result.scalar()
            logger.info(f"Memory summaries created: {summary_count}")
            
            logger.info("✅ Setup verification complete!")
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise


async def main():
    """Run all setup steps"""
    
    logger.info("=" * 60)
    logger.info("SARVAI Hierarchical Memory System Setup")
    logger.info("=" * 60)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Step 1: Classify existing memories
    await classify_existing_memories()
    
    # Step 2: Calculate importance scores
    await calculate_initial_importance()
    
    # Step 3: Run initial consolidation
    await run_initial_consolidation()
    
    # Step 4: Verify setup
    await verify_setup()
    
    logger.info("=" * 60)
    logger.info("Setup complete! Your memory system is ready.")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
