"""
Print Service for Professional Business Card Export
Game-Changing Feature: Digital → Print Ready Files
"""
import os
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from io import BytesIO
import base64

# PDF and image generation
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from PIL import Image, ImageDraw, ImageFont
import tempfile

# Template engine
from jinja2 import Template, Environment, BaseLoader

# Our models
from models.PrintExport import (
    PrintJob, PrintTemplate, PrintFormat, PrintSize, PrintQuality,
    PrintOrientation, QUALITY_SETTINGS, SIZE_SPECIFICATIONS, DEFAULT_TEMPLATES
)
from models.BusinessCard import BusinessCard

logger = logging.getLogger(__name__)


class PrintService:
    """Service for generating print-ready business card files"""
    
    def __init__(self):
        self.templates = {}
        self.quality_settings = QUALITY_SETTINGS
        self.size_specs = SIZE_SPECIFICATIONS
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default print templates"""
        for template_data in DEFAULT_TEMPLATES:
            template = PrintTemplate(**template_data)
            self.templates[template.id] = template
        
        logger.info(f"Loaded {len(self.templates)} default print templates")
    
    async def create_print_job(
        self,
        business_card: BusinessCard,
        template_id: str,
        format: PrintFormat = PrintFormat.PDF,
        quality: PrintQuality = PrintQuality.PRINT,
        **kwargs
    ) -> PrintJob:
        """
        Create a new print job for a business card
        """
        logger.info(f"Creating print job for card {business_card.id} with template {template_id}")
        
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Create print job
        job = PrintJob(
            user_id=str(business_card.user_id),
            business_card_id=str(business_card.id),
            template_id=template_id,
            format=format,
            size=template.size,
            orientation=template.orientation,
            quality=quality,
            **kwargs
        )
        
        try:
            # Generate the print files
            generated_files = await self._generate_print_files(business_card, template, job)
            
            job.generated_files = generated_files
            job.status = "completed"
            job.processing_completed_at = datetime.utcnow()
            
            # Generate preview
            preview_url = await self._generate_preview(business_card, template, job)
            job.preview_url = preview_url
            
            logger.info(f"Print job {job.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Print job {job.id} failed: {str(e)}")
            job.status = "failed"
            job.error_message = str(e)
        
        job.processing_completed_at = datetime.utcnow()
        return job
    
    async def _generate_print_files(
        self, 
        business_card: BusinessCard, 
        template: PrintTemplate, 
        job: PrintJob
    ) -> List[Dict[str, str]]:
        """
        Generate print-ready files in specified format
        """
        files = []
        
        if job.format == PrintFormat.PDF:
            pdf_file = await self._generate_pdf(business_card, template, job)
            files.append({
                "format": "pdf",
                "url": pdf_file,
                "filename": f"business_card_{business_card.name.replace(' ', '_')}.pdf",
                "size_mb": "0.5"  # Estimated size
            })
        
        elif job.format == PrintFormat.PNG:
            png_file = await self._generate_png(business_card, template, job)
            files.append({
                "format": "png",
                "url": png_file,
                "filename": f"business_card_{business_card.name.replace(' ', '_')}.png",
                "size_mb": "2.1"
            })
        
        elif job.format == PrintFormat.SVG:
            svg_file = await self._generate_svg(business_card, template, job)
            files.append({
                "format": "svg",
                "url": svg_file,
                "filename": f"business_card_{business_card.name.replace(' ', '_')}.svg",
                "size_mb": "0.1"
            })
        
        return files
    
    async def _generate_pdf(
        self, 
        business_card: BusinessCard, 
        template: PrintTemplate, 
        job: PrintJob
    ) -> str:
        """
        Generate PDF file for business card
        """
        # Get size specifications
        size_spec = self.size_specs[job.size]
        width_mm = size_spec["width"]
        height_mm = size_spec["height"]
        bleed_mm = size_spec["bleed"] if job.bleed_area else 0
        
        # Convert to points (1mm = 2.834645669 points)
        width_pt = (width_mm + 2 * bleed_mm) * 2.834645669
        height_pt = (height_mm + 2 * bleed_mm) * 2.834645669
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        
        # Create PDF canvas
        c = canvas.Canvas(temp_file.name, pagesize=(width_pt, height_pt))
        
        # Set quality-based DPI
        quality_config = self.quality_settings[job.quality]
        
        try:
            # Draw bleed area (if enabled)
            if job.bleed_area:
                bleed_pt = bleed_mm * 2.834645669
                c.setStrokeColor(HexColor("#00FF00"))  # Green for bleed
                c.setLineWidth(0.5)
                c.rect(bleed_pt, bleed_pt, width_mm * 2.834645669, height_mm * 2.834645669)
            
            # Draw background
            await self._draw_background(c, template, width_pt, height_pt, bleed_mm)
            
            # Draw content based on template layout
            await self._draw_card_content(c, business_card, template, width_pt, height_pt, bleed_mm)
            
            # Draw crop marks (if enabled)
            if job.crop_marks:
                await self._draw_crop_marks(c, width_pt, height_pt, bleed_mm)
            
            c.save()
            
            # Convert file to base64 URL (in real implementation, upload to storage)
            with open(temp_file.name, 'rb') as f:
                pdf_data = base64.b64encode(f.read()).decode()
                file_url = f"data:application/pdf;base64,{pdf_data}"
            
            # Clean up
            os.unlink(temp_file.name)
            
            logger.info(f"PDF generated successfully for card {business_card.id}")
            return file_url
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e
    
    async def _generate_png(
        self, 
        business_card: BusinessCard, 
        template: PrintTemplate, 
        job: PrintJob
    ) -> str:
        """
        Generate high-resolution PNG for business card
        """
        # Get size specifications
        size_spec = self.size_specs[job.size]
        quality_config = self.quality_settings[job.quality]
        
        dpi = quality_config["dpi"]
        width_mm = size_spec["width"]
        height_mm = size_spec["height"]
        bleed_mm = size_spec["bleed"] if job.bleed_area else 0
        
        # Calculate pixel dimensions
        width_px = int((width_mm + 2 * bleed_mm) * dpi / 25.4)  # 25.4mm = 1 inch
        height_px = int((height_mm + 2 * bleed_mm) * dpi / 25.4)
        
        # Create image
        img = Image.new('RGB', (width_px, height_px), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Draw background
            await self._draw_png_background(draw, img, template, width_px, height_px)
            
            # Draw content
            await self._draw_png_content(draw, img, business_card, template, width_px, height_px, dpi)
            
            # Save to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG', dpi=(dpi, dpi))
            img_data = base64.b64encode(buffer.getvalue()).decode()
            file_url = f"data:image/png;base64,{img_data}"
            
            logger.info(f"PNG generated successfully for card {business_card.id}")
            return file_url
            
        except Exception as e:
            logger.error(f"PNG generation failed: {e}")
            raise e
    
    async def _generate_svg(
        self, 
        business_card: BusinessCard, 
        template: PrintTemplate, 
        job: PrintJob
    ) -> str:
        """
        Generate SVG file for business card (vector format)
        """
        size_spec = self.size_specs[job.size]
        width_mm = size_spec["width"]
        height_mm = size_spec["height"]
        
        # Create SVG template
        svg_template = Template('''
        <svg width="{{ width }}mm" height="{{ height }}mm" 
             viewBox="0 0 {{ width }} {{ height }}" 
             xmlns="http://www.w3.org/2000/svg">
          
          <!-- Background -->
          <rect width="100%" height="100%" fill="{{ bg_color }}"/>
          
          <!-- Content -->
          <g id="content">
            <!-- Name -->
            <text x="{{ name_x }}" y="{{ name_y }}" 
                  font-family="{{ font_family }}" 
                  font-size="{{ name_size }}" 
                  font-weight="bold" 
                  fill="#000000">{{ name }}</text>
            
            <!-- Company -->
            <text x="{{ company_x }}" y="{{ company_y }}" 
                  font-family="{{ font_family }}" 
                  font-size="{{ company_size }}" 
                  fill="#333333">{{ company }}</text>
            
            <!-- Position -->
            <text x="{{ position_x }}" y="{{ position_y }}" 
                  font-family="{{ font_family }}" 
                  font-size="{{ position_size }}" 
                  fill="#666666">{{ position }}</text>
            
            <!-- Phone -->
            {% if phone %}
            <text x="{{ contact_x }}" y="{{ phone_y }}" 
                  font-family="{{ font_family }}" 
                  font-size="{{ contact_size }}" 
                  fill="#333333">{{ phone }}</text>
            {% endif %}
            
            <!-- Email -->
            {% if email %}
            <text x="{{ contact_x }}" y="{{ email_y }}" 
                  font-family="{{ font_family }}" 
                  font-size="{{ contact_size }}" 
                  fill="#333333">{{ email }}</text>
            {% endif %}
            
            <!-- Website -->
            {% if website %}
            <text x="{{ contact_x }}" y="{{ website_y }}" 
                  font-family="{{ font_family }}" 
                  font-size="{{ contact_size }}" 
                  fill="#0066CC">{{ website }}</text>
            {% endif %}
          </g>
        </svg>
        ''')
        
        # Extract business card data
        primary_phone = business_card.phones[0].number if business_card.phones else ""
        primary_email = business_card.emails[0].address if business_card.emails else ""
        
        # Render SVG
        svg_content = svg_template.render(
            width=width_mm,
            height=height_mm,
            bg_color=template.background_color or "#FFFFFF",
            font_family=template.font_family_primary,
            name=business_card.name,
            company=business_card.company or "",
            position=business_card.position or "",
            phone=primary_phone,
            email=primary_email,
            website=business_card.website or "",
            # Positioning (based on template layout)
            name_x=template.layout_config.get("name_position", {}).get("x", 10),
            name_y=template.layout_config.get("name_position", {}).get("y", 15),
            name_size=12,
            company_x=template.layout_config.get("company_position", {}).get("x", 10),
            company_y=template.layout_config.get("company_position", {}).get("y", 25),
            company_size=10,
            position_x=template.layout_config.get("company_position", {}).get("x", 10),
            position_y=template.layout_config.get("company_position", {}).get("y", 35),
            position_size=9,
            contact_x=template.layout_config.get("contact_position", {}).get("x", 10),
            contact_size=8,
            phone_y=45,
            email_y=52,
            website_y=59
        )
        
        # Convert to base64 URL
        svg_data = base64.b64encode(svg_content.encode()).decode()
        file_url = f"data:image/svg+xml;base64,{svg_data}"
        
        logger.info(f"SVG generated successfully for card {business_card.id}")
        return file_url
    
    async def _draw_background(self, c, template: PrintTemplate, width_pt: float, height_pt: float, bleed_mm: float):
        """Draw background for PDF"""
        if template.background_color:
            c.setFillColor(HexColor(template.background_color))
            c.rect(0, 0, width_pt, height_pt, fill=1, stroke=0)
    
    async def _draw_card_content(
        self, 
        c, 
        business_card: BusinessCard, 
        template: PrintTemplate, 
        width_pt: float, 
        height_pt: float, 
        bleed_mm: float
    ):
        """Draw business card content on PDF"""
        bleed_pt = bleed_mm * 2.834645669
        layout = template.layout_config
        
        # Set font
        c.setFont("Helvetica-Bold", 12)
        
        # Draw name
        name_pos = layout.get("name_position", {"x": 20, "y": 15})
        name_x = (name_pos["x"] + bleed_mm) * 2.834645669
        name_y = height_pt - (name_pos["y"] + bleed_mm) * 2.834645669
        
        c.setFillColor(HexColor("#000000"))
        c.drawString(name_x, name_y, business_card.name)
        
        # Draw company
        if business_card.company:
            c.setFont("Helvetica", 10)
            company_pos = layout.get("company_position", {"x": 20, "y": 30})
            company_x = (company_pos["x"] + bleed_mm) * 2.834645669
            company_y = height_pt - (company_pos["y"] + bleed_mm) * 2.834645669
            
            c.setFillColor(HexColor("#333333"))
            c.drawString(company_x, company_y, business_card.company)
        
        # Draw position
        if business_card.position:
            c.setFont("Helvetica", 9)
            position_x = (name_pos["x"] + bleed_mm) * 2.834645669
            position_y = height_pt - (name_pos["y"] + 10 + bleed_mm) * 2.834645669
            
            c.setFillColor(HexColor("#666666"))
            c.drawString(position_x, position_y, business_card.position)
        
        # Draw contact info
        c.setFont("Helvetica", 8)
        contact_pos = layout.get("contact_position", {"x": 20, "y": 45})
        contact_x = (contact_pos["x"] + bleed_mm) * 2.834645669
        contact_y = height_pt - (contact_pos["y"] + bleed_mm) * 2.834645669
        
        if business_card.phones:
            c.drawString(contact_x, contact_y, business_card.phones[0].number)
            contact_y -= 12
        
        if business_card.emails:
            c.drawString(contact_x, contact_y, business_card.emails[0].address)
            contact_y -= 12
        
        if business_card.website:
            c.setFillColor(HexColor("#0066CC"))
            c.drawString(contact_x, contact_y, business_card.website)
    
    async def _draw_png_background(self, draw, img, template: PrintTemplate, width_px: int, height_px: int):
        """Draw background for PNG"""
        if template.background_color:
            # Fill entire image with background color
            draw.rectangle([0, 0, width_px, height_px], fill=template.background_color)
    
    async def _draw_png_content(
        self, 
        draw, 
        img, 
        business_card: BusinessCard, 
        template: PrintTemplate, 
        width_px: int, 
        height_px: int, 
        dpi: int
    ):
        """Draw business card content on PNG"""
        layout = template.layout_config
        
        # Calculate scaling factor from mm to pixels
        scale = dpi / 25.4  # pixels per mm
        
        try:
            # Try to use custom font (fallback to default if not available)
            font_large = ImageFont.truetype("arial.ttf", int(12 * scale / 72 * dpi)) if os.path.exists("arial.ttf") else ImageFont.load_default()
            font_medium = ImageFont.truetype("arial.ttf", int(10 * scale / 72 * dpi)) if os.path.exists("arial.ttf") else ImageFont.load_default()  
            font_small = ImageFont.truetype("arial.ttf", int(8 * scale / 72 * dpi)) if os.path.exists("arial.ttf") else ImageFont.load_default()
        except:
            # Use default fonts if custom fonts fail
            font_large = font_medium = font_small = ImageFont.load_default()
        
        # Draw name
        name_pos = layout.get("name_position", {"x": 20, "y": 15})
        name_x = int(name_pos["x"] * scale)
        name_y = int(name_pos["y"] * scale)
        
        draw.text((name_x, name_y), business_card.name, fill="#000000", font=font_large)
        
        # Draw company
        if business_card.company:
            company_pos = layout.get("company_position", {"x": 20, "y": 30})
            company_x = int(company_pos["x"] * scale)
            company_y = int(company_pos["y"] * scale)
            
            draw.text((company_x, company_y), business_card.company, fill="#333333", font=font_medium)
        
        # Draw position
        if business_card.position:
            position_x = name_x
            position_y = name_y + int(12 * scale)
            
            draw.text((position_x, position_y), business_card.position, fill="#666666", font=font_small)
        
        # Draw contact info
        contact_pos = layout.get("contact_position", {"x": 20, "y": 45})
        contact_x = int(contact_pos["x"] * scale)
        contact_y = int(contact_pos["y"] * scale)
        
        if business_card.phones:
            draw.text((contact_x, contact_y), business_card.phones[0].number, fill="#333333", font=font_small)
            contact_y += int(10 * scale)
        
        if business_card.emails:
            draw.text((contact_x, contact_y), business_card.emails[0].address, fill="#333333", font=font_small)
            contact_y += int(10 * scale)
        
        if business_card.website:
            draw.text((contact_x, contact_y), business_card.website, fill="#0066CC", font=font_small)
    
    async def _draw_crop_marks(self, c, width_pt: float, height_pt: float, bleed_mm: float):
        """Draw crop marks for PDF"""
        bleed_pt = bleed_mm * 2.834645669
        mark_length = 5 * 2.834645669  # 5mm marks
        
        c.setStrokeColor(HexColor("#000000"))
        c.setLineWidth(0.5)
        
        # Top left
        c.line(bleed_pt - mark_length, bleed_pt, bleed_pt, bleed_pt)
        c.line(bleed_pt, bleed_pt - mark_length, bleed_pt, bleed_pt)
        
        # Top right
        c.line(width_pt - bleed_pt + mark_length, bleed_pt, width_pt - bleed_pt, bleed_pt)
        c.line(width_pt - bleed_pt, bleed_pt - mark_length, width_pt - bleed_pt, bleed_pt)
        
        # Bottom left
        c.line(bleed_pt - mark_length, height_pt - bleed_pt, bleed_pt, height_pt - bleed_pt)
        c.line(bleed_pt, height_pt - bleed_pt + mark_length, bleed_pt, height_pt - bleed_pt)
        
        # Bottom right
        c.line(width_pt - bleed_pt + mark_length, height_pt - bleed_pt, width_pt - bleed_pt, height_pt - bleed_pt)
        c.line(width_pt - bleed_pt, height_pt - bleed_pt + mark_length, width_pt - bleed_pt, height_pt - bleed_pt)
    
    async def _generate_preview(
        self, 
        business_card: BusinessCard, 
        template: PrintTemplate, 
        job: PrintJob
    ) -> str:
        """
        Generate low-res preview image
        """
        # Generate a small PNG preview (72 DPI for web)
        preview_job = PrintJob(
            user_id=job.user_id,
            business_card_id=job.business_card_id,
            template_id=job.template_id,
            format=PrintFormat.PNG,
            quality=PrintQuality.WEB,
            size=job.size,
            bleed_area=False,
            crop_marks=False
        )
        
        return await self._generate_png(business_card, template, preview_job)
    
    async def get_templates(self, category: Optional[str] = None) -> List[PrintTemplate]:
        """
        Get available print templates
        """
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    async def get_template_categories(self) -> List[str]:
        """
        Get available template categories
        """
        categories = set(t.category for t in self.templates.values())
        return sorted(list(categories))


# Singleton service instance
print_service = PrintService()