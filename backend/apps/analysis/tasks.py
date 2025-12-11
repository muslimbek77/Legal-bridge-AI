"""
Celery tasks for contract analysis.
"""

import time
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def analyze_contract_task(self, contract_id: str):
    """
    Asynchronous task for analyzing a contract.
    """
    from apps.contracts.models import Contract
    from apps.analysis.models import AnalysisResult
    from ai_engine.pipeline import ContractAnalysisPipeline
    
    try:
        contract = Contract.objects.get(id=contract_id)
        logger.info(f"Starting analysis for contract: {contract_id}")
        
        start_time = time.time()
        
        # Create analysis result
        analysis = AnalysisResult.objects.create(
            contract=contract,
            status=AnalysisResult.AnalysisStatus.IN_PROGRESS
        )
        
        # Initialize AI pipeline
        pipeline = ContractAnalysisPipeline()
        
        # Run analysis
        result = pipeline.analyze(contract)
        
        # Update analysis result
        analysis.overall_score = result.get('overall_score', 0)
        analysis.compliance_score = result.get('compliance_score', 0)
        analysis.completeness_score = result.get('completeness_score', 0)
        analysis.clarity_score = result.get('clarity_score', 0)
        analysis.balance_score = result.get('balance_score', 0)
        analysis.summary = result.get('summary', '')
        analysis.recommendations = result.get('recommendations', [])
        analysis.model_used = result.get('model_used', 'llama3.1')
        analysis.processing_time = time.time() - start_time
        analysis.status = AnalysisResult.AnalysisStatus.COMPLETED
        analysis.completed_at = timezone.now()
        analysis.save()
        
        # Create compliance issues
        from apps.analysis.models import ComplianceIssue
        for issue_data in result.get('issues', []):
            ComplianceIssue.objects.create(
                analysis=analysis,
                issue_type=issue_data.get('type', 'other'),
                severity=issue_data.get('severity', 'medium'),
                title=issue_data.get('title', ''),
                description=issue_data.get('description', ''),
                section_reference=issue_data.get('section', ''),
                clause_reference=issue_data.get('clause', ''),
                text_excerpt=issue_data.get('text_excerpt', ''),
                law_name=issue_data.get('law_name', ''),
                law_article=issue_data.get('law_article', ''),
                suggestion=issue_data.get('suggestion', ''),
                suggested_text=issue_data.get('suggested_text', '')
            )
        
        # Update contract status
        contract.status = Contract.Status.ANALYZED
        contract.analyzed_at = timezone.now()
        contract.save()
        
        logger.info(f"Analysis completed for contract: {contract_id}")
        return str(analysis.id)
        
    except Contract.DoesNotExist:
        logger.error(f"Contract not found: {contract_id}")
        raise
        
    except Exception as exc:
        logger.error(f"Analysis failed for contract {contract_id}: {exc}")
        
        # Update analysis status if exists
        try:
            analysis = AnalysisResult.objects.filter(
                contract_id=contract_id,
                status=AnalysisResult.AnalysisStatus.IN_PROGRESS
            ).latest('created_at')
            analysis.status = AnalysisResult.AnalysisStatus.FAILED
            analysis.error_message = str(exc)
            analysis.save()
        except AnalysisResult.DoesNotExist:
            pass
        
        # Retry task
        self.retry(exc=exc, countdown=60)


@shared_task
def batch_analyze_contracts(contract_ids: list):
    """
    Analyze multiple contracts in batch.
    """
    results = []
    for contract_id in contract_ids:
        result = analyze_contract_task.delay(contract_id)
        results.append(result.id)
    return results


@shared_task
def cleanup_old_analyses(days: int = 90):
    """
    Clean up old analysis results.
    """
    from apps.analysis.models import AnalysisResult
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = AnalysisResult.objects.filter(
        created_at__lt=cutoff_date,
        status=AnalysisResult.AnalysisStatus.COMPLETED
    ).delete()
    
    logger.info(f"Deleted {deleted_count} old analysis results")
    return deleted_count
