"""
Campaign Builder Service
Generates marketing campaign assets using LLM
"""
import os
import json
import uuid
import zipfile
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from .llm_provider import llm_service
from .rag_client import rag_client

logger = logging.getLogger(__name__)

class CampaignBuilder:
    """Generates complete marketing campaign assets"""
    
    SYSTEM_MESSAGE = """És um especialista em marketing digital e copywriting de alta conversão.
Crias conteúdo persuasivo, profissional e orientado a resultados.
Responde sempre no idioma solicitado.
Segue as instruções exactamente e formata o output conforme pedido."""

    async def generate_campaign(
        self,
        niche: str,
        product: str,
        offer: str,
        price: str,
        objective: str,  # leads / vendas
        tone: str,
        channel: str,  # IG / FB / Google / email
        language: str = "pt",
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """Generate complete campaign package"""
        
        campaign_id = f"camp_{uuid.uuid4().hex[:12]}"
        
        # Get RAG context if enabled
        rag_context = ""
        if use_rag:
            query = f"{niche} {product} marketing {channel}"
            docs = await rag_client.retrieve(query)
            rag_context = rag_client.format_context(docs)
        
        # Generate all assets
        landing_copy = await self._generate_landing_copy(
            niche, product, offer, price, objective, tone, language, rag_context
        )
        
        ad_variations = await self._generate_ad_variations(
            niche, product, offer, price, objective, tone, channel, language, rag_context
        )
        
        creative_ideas = await self._generate_creative_ideas(
            niche, product, offer, channel, tone, language
        )
        
        email_sequence = await self._generate_email_sequence(
            niche, product, offer, price, objective, tone, language, rag_context
        )
        
        checklist = await self._generate_checklist(
            channel, objective, language
        )
        
        return {
            "campaign_id": campaign_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config": {
                "niche": niche,
                "product": product,
                "offer": offer,
                "price": price,
                "objective": objective,
                "tone": tone,
                "channel": channel,
                "language": language
            },
            "assets": {
                "landing_copy": landing_copy,
                "ad_variations": ad_variations,
                "creative_ideas": creative_ideas,
                "email_sequence": email_sequence,
                "checklist": checklist
            },
            "rag_used": bool(rag_context)
        }
    
    async def _generate_landing_copy(
        self, niche: str, product: str, offer: str, price: str,
        objective: str, tone: str, language: str, rag_context: str
    ) -> Dict[str, Any]:
        """Generate landing page copy"""
        
        prompt = f"""{rag_context}

Cria copy para uma landing page de venda com os seguintes dados:
- Nicho: {niche}
- Produto: {product}
- Oferta: {offer}
- Preço: {price}
- Objetivo: {objective}
- Tom: {tone}
- Idioma: {language}

Gera em formato JSON válido:
{{
    "headline": "Título principal (máx 10 palavras)",
    "subheadline": "Subtítulo que reforça valor (máx 20 palavras)",
    "hero_text": "Parágrafo de abertura (2-3 frases)",
    "bullets": ["Benefício 1", "Benefício 2", "Benefício 3", "Benefício 4", "Benefício 5"],
    "social_proof": "Frase de prova social",
    "cta_primary": "Texto do botão principal",
    "cta_secondary": "Texto alternativo",
    "urgency": "Elemento de urgência/escassez",
    "guarantee": "Garantia oferecida",
    "faq": [
        {{"q": "Pergunta 1", "a": "Resposta 1"}},
        {{"q": "Pergunta 2", "a": "Resposta 2"}},
        {{"q": "Pergunta 3", "a": "Resposta 3"}}
    ]
}}

IMPORTANTE: Responde APENAS com JSON válido, sem texto adicional."""

        response = await llm_service.generate(prompt, self.SYSTEM_MESSAGE, max_tokens=2000)
        return self._parse_json_response(response)
    
    async def _generate_ad_variations(
        self, niche: str, product: str, offer: str, price: str,
        objective: str, tone: str, channel: str, language: str, rag_context: str
    ) -> List[Dict[str, str]]:
        """Generate 5 ad text variations"""
        
        prompt = f"""{rag_context}

Cria 5 variações de anúncios para {channel}:
- Nicho: {niche}
- Produto: {product}
- Oferta: {offer}
- Preço: {price}
- Objetivo: {objective}
- Tom: {tone}
- Idioma: {language}

Gera em formato JSON válido - array de 5 objetos:
[
    {{
        "hook": "Gancho inicial (1 frase impactante)",
        "body": "Corpo do anúncio (2-3 frases)",
        "cta": "Call to action",
        "style": "Estilo usado (ex: curiosidade, dor, benefício, etc.)"
    }},
    ... (mais 4 variações)
]

IMPORTANTE: Responde APENAS com JSON válido, sem texto adicional."""

        response = await llm_service.generate(prompt, self.SYSTEM_MESSAGE, max_tokens=2000)
        result = self._parse_json_response(response)
        return result if isinstance(result, list) else []
    
    async def _generate_creative_ideas(
        self, niche: str, product: str, offer: str,
        channel: str, tone: str, language: str
    ) -> List[Dict[str, str]]:
        """Generate 5 creative/visual ideas"""
        
        prompt = f"""Cria 5 ideias de criativos/visuais para anúncios em {channel}:
- Nicho: {niche}
- Produto: {product}
- Oferta: {offer}
- Tom: {tone}
- Idioma: {language}

Gera em formato JSON válido - array de 5 objetos:
[
    {{
        "concept": "Conceito do criativo",
        "visual_description": "Descrição detalhada do visual (o que mostrar)",
        "text_overlay": "Texto a colocar sobre a imagem",
        "format": "Formato sugerido (carrossel, vídeo curto, imagem única, etc.)"
    }},
    ... (mais 4 ideias)
]

IMPORTANTE: Responde APENAS com JSON válido, sem texto adicional."""

        response = await llm_service.generate(prompt, self.SYSTEM_MESSAGE, max_tokens=2000)
        result = self._parse_json_response(response)
        return result if isinstance(result, list) else []
    
    async def _generate_email_sequence(
        self, niche: str, product: str, offer: str, price: str,
        objective: str, tone: str, language: str, rag_context: str
    ) -> List[Dict[str, str]]:
        """Generate 5-email sequence"""
        
        prompt = f"""{rag_context}

Cria uma sequência de 5 emails de vendas:
- Nicho: {niche}
- Produto: {product}
- Oferta: {offer}
- Preço: {price}
- Objetivo: {objective}
- Tom: {tone}
- Idioma: {language}

Sequência:
1) Email de boas-vindas + introdução ao problema
2) Email educativo + agitação do problema
3) Email de solução + apresentação do produto
4) Email de prova social + objeções
5) Email de urgência + última chamada

Gera em formato JSON válido - array de 5 objetos:
[
    {{
        "day": 1,
        "purpose": "Objetivo do email",
        "subject_line": "Linha de assunto",
        "preview_text": "Texto de preview",
        "body": "Corpo do email completo (3-5 parágrafos)",
        "cta": "Call to action"
    }},
    ... (mais 4 emails)
]

IMPORTANTE: Responde APENAS com JSON válido, sem texto adicional."""

        response = await llm_service.generate(prompt, self.SYSTEM_MESSAGE, max_tokens=4000)
        result = self._parse_json_response(response)
        return result if isinstance(result, list) else []
    
    async def _generate_checklist(
        self, channel: str, objective: str, language: str
    ) -> List[Dict[str, Any]]:
        """Generate publication checklist"""
        
        prompt = f"""Cria um checklist passo-a-passo para lançar uma campanha em {channel}:
- Objetivo: {objective}
- Idioma: {language}

Gera em formato JSON válido - array de tarefas ordenadas:
[
    {{
        "step": 1,
        "task": "Descrição da tarefa",
        "details": "Detalhes ou dicas adicionais",
        "priority": "alta/média/baixa"
    }},
    ... (10-15 tarefas)
]

IMPORTANTE: Responde APENAS com JSON válido, sem texto adicional."""

        response = await llm_service.generate(prompt, self.SYSTEM_MESSAGE, max_tokens=2000)
        result = self._parse_json_response(response)
        return result if isinstance(result, list) else []
    
    def _parse_json_response(self, response: str) -> Any:
        """Parse JSON from LLM response"""
        # Clean response
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {"error": "Failed to parse response", "raw": text[:500]}
    
    def export_to_files(self, campaign: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
        """Export campaign to files (JSON + Markdown)"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files_created = {}
        
        # Export full JSON
        json_path = output_dir / "campaign.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(campaign, f, ensure_ascii=False, indent=2)
        files_created["campaign.json"] = str(json_path)
        
        # Export Markdown versions
        assets = campaign.get("assets", {})
        config = campaign.get("config", {})
        
        # Landing copy markdown
        if "landing_copy" in assets:
            md_content = self._landing_to_markdown(assets["landing_copy"], config)
            md_path = output_dir / "landing_copy.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            files_created["landing_copy.md"] = str(md_path)
        
        # Ads markdown
        if "ad_variations" in assets:
            md_content = self._ads_to_markdown(assets["ad_variations"], config)
            md_path = output_dir / "ad_variations.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            files_created["ad_variations.md"] = str(md_path)
        
        # Creative ideas markdown
        if "creative_ideas" in assets:
            md_content = self._creatives_to_markdown(assets["creative_ideas"], config)
            md_path = output_dir / "creative_ideas.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            files_created["creative_ideas.md"] = str(md_path)
        
        # Email sequence markdown
        if "email_sequence" in assets:
            md_content = self._emails_to_markdown(assets["email_sequence"], config)
            md_path = output_dir / "email_sequence.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            files_created["email_sequence.md"] = str(md_path)
        
        # Checklist markdown
        if "checklist" in assets:
            md_content = self._checklist_to_markdown(assets["checklist"], config)
            md_path = output_dir / "checklist.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            files_created["checklist.md"] = str(md_path)
        
        return files_created
    
    def create_zip(self, campaign: Dict[str, Any]) -> bytes:
        """Create ZIP file with all campaign assets"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "campaign"
            self.export_to_files(campaign, output_dir)
            
            zip_path = Path(tmpdir) / "campaign.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in output_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(output_dir)
                        zf.write(file_path, arcname)
            
            return zip_path.read_bytes()
    
    def _landing_to_markdown(self, data: Dict, config: Dict) -> str:
        if isinstance(data, dict) and "error" in data:
            return f"# Error\n{data.get('error')}\n\n```\n{data.get('raw', '')}\n```"
        
        return f"""# Landing Page Copy
**Produto:** {config.get('product', 'N/A')}
**Oferta:** {config.get('offer', 'N/A')}

---

## Headline
{data.get('headline', 'N/A')}

## Subheadline
{data.get('subheadline', 'N/A')}

## Hero Text
{data.get('hero_text', 'N/A')}

## Benefícios
{chr(10).join(f"- {b}" for b in data.get('bullets', []))}

## Prova Social
{data.get('social_proof', 'N/A')}

## CTAs
- **Primário:** {data.get('cta_primary', 'N/A')}
- **Secundário:** {data.get('cta_secondary', 'N/A')}

## Urgência
{data.get('urgency', 'N/A')}

## Garantia
{data.get('guarantee', 'N/A')}

## FAQ
{chr(10).join(f"**Q: {faq.get('q', '')}**{chr(10)}A: {faq.get('a', '')}{chr(10)}" for faq in data.get('faq', []))}
"""
    
    def _ads_to_markdown(self, data: List, config: Dict) -> str:
        if not isinstance(data, list):
            return "# Error\nInvalid data format"
        
        content = f"""# Variações de Anúncios
**Canal:** {config.get('channel', 'N/A')}
**Produto:** {config.get('product', 'N/A')}

---

"""
        for i, ad in enumerate(data, 1):
            content += f"""## Variação {i} ({ad.get('style', 'N/A')})

**Hook:** {ad.get('hook', 'N/A')}

**Body:**
{ad.get('body', 'N/A')}

**CTA:** {ad.get('cta', 'N/A')}

---

"""
        return content
    
    def _creatives_to_markdown(self, data: List, config: Dict) -> str:
        if not isinstance(data, list):
            return "# Error\nInvalid data format"
        
        content = f"""# Ideias de Criativos
**Canal:** {config.get('channel', 'N/A')}
**Produto:** {config.get('product', 'N/A')}

---

"""
        for i, creative in enumerate(data, 1):
            content += f"""## Ideia {i}

**Conceito:** {creative.get('concept', 'N/A')}

**Descrição Visual:**
{creative.get('visual_description', 'N/A')}

**Texto Overlay:** {creative.get('text_overlay', 'N/A')}

**Formato:** {creative.get('format', 'N/A')}

---

"""
        return content
    
    def _emails_to_markdown(self, data: List, config: Dict) -> str:
        if not isinstance(data, list):
            return "# Error\nInvalid data format"
        
        content = f"""# Sequência de Emails
**Produto:** {config.get('product', 'N/A')}
**Oferta:** {config.get('offer', 'N/A')}

---

"""
        for email in data:
            content += f"""## Dia {email.get('day', '?')} - {email.get('purpose', 'N/A')}

**Subject:** {email.get('subject_line', 'N/A')}

**Preview:** {email.get('preview_text', 'N/A')}

**Body:**
{email.get('body', 'N/A')}

**CTA:** {email.get('cta', 'N/A')}

---

"""
        return content
    
    def _checklist_to_markdown(self, data: List, config: Dict) -> str:
        if not isinstance(data, list):
            return "# Error\nInvalid data format"
        
        content = f"""# Checklist de Publicação
**Canal:** {config.get('channel', 'N/A')}
**Objetivo:** {config.get('objective', 'N/A')}

---

"""
        for item in data:
            priority_emoji = {"alta": "🔴", "média": "🟡", "baixa": "🟢"}.get(item.get("priority", ""), "⚪")
            content += f"""- [ ] **{item.get('step', '?')}. {item.get('task', 'N/A')}** {priority_emoji}
  {item.get('details', '')}

"""
        return content

# Global instance
campaign_builder = CampaignBuilder()
