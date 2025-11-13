"""Test the full QA pipeline to verify end-to-end functionality."""

import asyncio
import os
import sys
import json

# Set environment variables before importing
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from app.services.qa_service import QAService
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def test_qa_pipeline():
    """Test the complete QA pipeline."""
    print("=" * 70)
    print("Testing Complete QA Pipeline")
    print("=" * 70)
    
    qa_service = QAService()
    
    # Test questions
    test_questions = [
        "Who is planning a trip to Paris?",
        "What is Sophia Al-Farsi requesting?",
        "Who needs tickets to the opera in Milan?",
    ]
    
    try:
        for idx, question in enumerate(test_questions, 1):
            print(f"\n{'='*70}")
            print(f"Test {idx}/{len(test_questions)}")
            print(f"{'='*70}")
            print(f"Question: {question}")
            print("-" * 70)
            
            try:
                answer, source_ids = await qa_service.answer_question(question)
                
                print(f"\n✅ Answer:")
                print(f"   {answer}")
                print(f"\n📚 Sources ({len(source_ids)} message IDs):")
                for i, source_id in enumerate(source_ids[:5], 1):  # Show first 5
                    print(f"   {i}. {source_id}")
                if len(source_ids) > 5:
                    print(f"   ... and {len(source_ids) - 5} more")
                
            except Exception as e:
                print(f"\n❌ Error processing question:")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*70}")
        print("✅ QA Pipeline Test Complete")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Fatal error in QA pipeline:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await qa_service.close()


if __name__ == "__main__":
    asyncio.run(test_qa_pipeline())

