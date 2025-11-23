"""Generate human-readable reports from image search results."""
from src.domain.search_entities import (
    ImageSearchReport,
    SearchStatus
)


class SearchReportGenerator:
    """Generate formatted reports from search results."""
    
    def generate_text_report(
        self, 
        report: ImageSearchReport
    ) -> str:
        """Generate text-based search report."""
        lines = []
        lines.append("=" * 60)
        lines.append("IMAGE SEARCH REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Image: {report.image_path}")
        lines.append(
            f"Search Duration: {self._format_duration(report)}"
        )
        lines.append("")
        lines.append("SOURCES SEARCHED:")
        lines.append("-" * 60)
        
        for source in report.sources_searched:
            lines.append(f"  • {source.value}")
        
        lines.append("")
        lines.append("SEARCH RESULTS:")
        lines.append("-" * 60)
        
        if report.was_found():
            lines.append(
                f"✓ IMAGE FOUND - {report.total_matches} match(es)"
            )
            lines.append("")
            
            for result in report.results_found:
                if result.status == SearchStatus.SUCCESS:
                    lines.append(f"Source: {result.source.value}")
                    lines.append(f"  Title: {result.page_title}")
                    lines.append(f"  URL: {result.page_url}")
                    if result.similarity_score:
                        score_pct = result.similarity_score * 100
                        lines.append(
                            f"  Similarity: {score_pct:.1f}%"
                        )
                    lines.append("")
        else:
            lines.append("✗ IMAGE NOT FOUND")
            lines.append("")
            lines.append("No matches found in any source.")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _format_duration(
        self, 
        report: ImageSearchReport
    ) -> str:
        """Format search duration."""
        if not report.search_completed:
            return "In progress"
        
        duration = (
            report.search_completed - report.search_started
        )
        seconds = duration.total_seconds()
        return f"{seconds:.2f} seconds"
