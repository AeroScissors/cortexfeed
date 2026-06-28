# File: cortexfeed/investigation/prompts/composer_v2.py
from typing import Any

class PromptComposerV2:
    MAX_FILES = 20
    MAX_SYMBOLS = 30
    MAX_DEPENDENCIES = 50
    MAX_CALL_CHAINS = 20

    def _format_files(self, context: Any) -> str:
        if not context.files:
            return ""
        
        lines = ["RELEVANT FILES", ""]
        for f in context.files[:self.MAX_FILES]:
            path = f.path if hasattr(f, 'path') else f.get('path', str(f)) if isinstance(f, dict) else str(f)
            lines.append(f"- {path}")
        return "\n".join(lines)

    def _format_symbols(self, context: Any) -> str:
        if not context.symbols:
            return ""
        
        lines = ["RELEVANT SYMBOLS", ""]
        for sym in context.symbols[:self.MAX_SYMBOLS]:
            lines.append(f"- {sym}")
        return "\n".join(lines)

    def _format_dependencies(self, context: Any) -> str:
        if not context.dependencies:
            return ""
        
        lines = ["DEPENDENCIES", ""]
        for dep in context.dependencies[:self.MAX_DEPENDENCIES]:
            source = dep.source if hasattr(dep, 'source') else dep.get('source', '') if isinstance(dep, dict) else ""
            target = dep.target if hasattr(dep, 'target') else dep.get('target', '') if isinstance(dep, dict) else ""
            if source and target:
                lines.append(f"{source}\n  -> {target}\n")
        return "\n".join(lines).strip()

    def _format_call_chains(self, context: Any) -> str:
        if not context.call_chains:
            return ""
        
        lines = ["EXECUTION PATHS", ""]
        for cc in context.call_chains[:self.MAX_CALL_CHAINS]:
            chain = cc.chain if hasattr(cc, 'chain') else cc.get('chain', []) if isinstance(cc, dict) else cc
            if isinstance(chain, list):
                lines.append("\n \u2193\n".join(chain) + "\n")
        return "\n".join(lines).strip()

    def _format_routes(self, context: Any) -> str:
        if not context.routes:
            return ""
        
        lines = ["ROUTE CONTEXT", ""]
        for route in context.routes:
            lines.append(route)
        return "\n".join(lines)

    def _format_facts(self, facts: list[Any]) -> str:
        if not facts:
            return ""
        
        lines = ["FACTS", ""]
        for fact in facts:
            content = fact.content if hasattr(fact, 'content') else fact.get('content', str(fact)) if isinstance(fact, dict) else str(fact)
            lines.append(f"- {content}")
        return "\n".join(lines)

    def _format_hypotheses(self, hypotheses: list[Any]) -> str:
        if not hypotheses:
            return ""
        
        lines = ["HYPOTHESES", ""]
        for i, hyp in enumerate(hypotheses, 1):
            content = hyp.content if hasattr(hyp, 'content') else hyp.get('content', str(hyp)) if isinstance(hyp, dict) else str(hyp)
            lines.append(f"{i}. {content}")
        return "\n".join(lines)

    def compose(
        self,
        issue: str,
        context: Any,
        facts: list[Any],
        hypotheses: list[Any],
    ) -> str:
        sections = []

        sections.append(f"INVESTIGATION ISSUE\n\n{issue}")

        files_section = self._format_files(context)
        if files_section:
            sections.append(files_section)

        symbols_section = self._format_symbols(context)
        if symbols_section:
            sections.append(symbols_section)

        deps_section = self._format_dependencies(context)
        if deps_section:
            sections.append(deps_section)

        chains_section = self._format_call_chains(context)
        if chains_section:
            sections.append(chains_section)

        routes_section = self._format_routes(context)
        if routes_section:
            sections.append(routes_section)

        facts_section = self._format_facts(facts)
        if facts_section:
            sections.append(facts_section)

        hypotheses_section = self._format_hypotheses(hypotheses)
        if hypotheses_section:
            sections.append(hypotheses_section)

        instructions = (
            "INVESTIGATION INSTRUCTIONS\n\n"
            "Use the supplied repository intelligence.\n\n"
            "Reason using:\n"
            "- execution paths\n"
            "- dependency relationships\n"
            "- route traces\n"
            "- collected evidence\n\n"
            "Do not speculate beyond the provided context."
        )
        sections.append(instructions)

        return "\n\n".join(sections)