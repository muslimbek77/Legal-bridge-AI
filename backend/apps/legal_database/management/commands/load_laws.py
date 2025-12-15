"""
Management command to load laws and legal data from JSON files.
Usage: python manage.py load_laws
"""

import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.legal_database.models import Law, LawChapter, LawArticle, LegalRule, ContractTemplate


class Command(BaseCommand):
    help = "O'zbekiston qonunlarini JSON fayllardan yuklash"

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='apps/legal_database/data',
            help="Ma'lumotlar joylashgan papka"
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help="Avvalgi ma'lumotlarni o'chirish"
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        
        if not data_dir.exists():
            self.stderr.write(self.style.ERROR(f"Papka topilmadi: {data_dir}"))
            return
        
        if options['clear']:
            self.stdout.write("Avvalgi ma'lumotlar o'chirilmoqda...")
            LegalRule.objects.all().delete()
            LawArticle.objects.all().delete()
            LawChapter.objects.all().delete()
            Law.objects.all().delete()
            ContractTemplate.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Ma'lumotlar o'chirildi"))
        
        # Load laws
        laws_file = data_dir / 'laws.json'
        if laws_file.exists():
            self.load_laws(laws_file)
        
        # Load contract templates
        templates_file = data_dir / 'contract_templates.json'
        if templates_file.exists():
            self.load_templates(templates_file)
        
        # Load legal rules
        rules_file = data_dir / 'legal_rules.json'
        if rules_file.exists():
            self.load_rules(rules_file)
        
        self.stdout.write(self.style.SUCCESS("Barcha ma'lumotlar yuklandi!"))
    
    @transaction.atomic
    def load_laws(self, file_path):
        """Load laws from JSON file."""
        self.stdout.write(f"Qonunlar yuklanmoqda: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        laws_count = 0
        articles_count = 0
        
        for law_data in data.get('laws', []):
            # Create or update law
            law, created = Law.objects.update_or_create(
                short_name=law_data.get('short_name', ''),
                defaults={
                    'name': law_data['name'],
                    'name_ru': law_data.get('name_ru', ''),
                    'law_type': law_data.get('law_type', 'law'),
                    'number': law_data.get('number', ''),
                    'adoption_date': law_data.get('adoption_date'),
                    'effective_date': law_data.get('effective_date'),
                    'status': law_data.get('status', 'active'),
                    'description': law_data.get('description', ''),
                    'source_url': law_data.get('source_url', ''),
                }
            )
            laws_count += 1
            
            # Load chapters
            chapters_map = {}
            for chapter_data in law_data.get('chapters', []):
                chapter, _ = LawChapter.objects.update_or_create(
                    law=law,
                    number=chapter_data['number'],
                    defaults={
                        'title': chapter_data['title'],
                        'title_ru': chapter_data.get('title_ru', ''),
                        'order': chapter_data.get('order', 0),
                    }
                )
                chapters_map[chapter_data['number']] = chapter
            
            # Load articles
            for article_data in law_data.get('articles', []):
                chapter = None
                if article_data.get('chapter_number'):
                    chapter = chapters_map.get(article_data['chapter_number'])
                
                article, _ = LawArticle.objects.update_or_create(
                    law=law,
                    number=article_data['number'],
                    defaults={
                        'chapter': chapter,
                        'title': article_data['title'],
                        'title_ru': article_data.get('title_ru', ''),
                        'content': article_data['content'],
                        'content_ru': article_data.get('content_ru', ''),
                        'is_mandatory': article_data.get('is_mandatory', False),
                        'applies_to': article_data.get('applies_to', []),
                        'keywords': article_data.get('keywords', []),
                        'order': article_data.get('order', 0),
                    }
                )
                articles_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Yuklandi: {laws_count} ta qonun, {articles_count} ta modda"
        ))
    
    @transaction.atomic
    def load_templates(self, file_path):
        """Load contract templates from JSON file."""
        self.stdout.write(f"Shartnoma shablonlari yuklanmoqda: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for template_data in data.get('templates', []):
            template, _ = ContractTemplate.objects.update_or_create(
                name=template_data['name'],
                defaults={
                    'contract_type': template_data['contract_type'],
                    'description': template_data.get('description', ''),
                    'template_text': template_data.get('template_text', ''),
                    'required_sections': template_data.get('required_sections', []),
                    'is_approved': template_data.get('is_approved', True),
                }
            )
            
            # Link related laws
            if template_data.get('related_laws'):
                laws = Law.objects.filter(short_name__in=template_data['related_laws'])
                template.related_laws.set(laws)
            
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Yuklandi: {count} ta shablon"))
    
    @transaction.atomic
    def load_rules(self, file_path):
        """Load legal rules from JSON file."""
        self.stdout.write(f"Huquqiy qoidalar yuklanmoqda: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for rule_data in data.get('rules', []):
            # Find the article
            article = LawArticle.objects.filter(
                law__short_name=rule_data['law_short_name'],
                number=rule_data['article_number']
            ).first()
            
            if not article:
                self.stderr.write(self.style.WARNING(
                    f"Modda topilmadi: {rule_data['law_short_name']} - {rule_data['article_number']}"
                ))
                continue
            
            rule, _ = LegalRule.objects.update_or_create(
                article=article,
                title=rule_data['title'],
                defaults={
                    'rule_type': rule_data['rule_type'],
                    'severity': rule_data.get('severity', 'medium'),
                    'description': rule_data['description'],
                    'condition': rule_data.get('condition', ''),
                    'validation_pattern': rule_data.get('validation_pattern', ''),
                    'applies_to_contract_types': rule_data.get('applies_to_contract_types', []),
                    'suggestion_template': rule_data.get('suggestion_template', ''),
                    'is_active': rule_data.get('is_active', True),
                }
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Yuklandi: {count} ta qoida"))
