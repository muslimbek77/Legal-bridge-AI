"""
Management command to index laws into vector store for RAG.
Usage: python manage.py index_laws
"""

import logging
from django.core.management.base import BaseCommand
from apps.legal_database.models import Law, LawArticle

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Qonunlarni vector store ga yuklash (RAG uchun)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help="Avvalgi indekslarni tozalash"
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help="Bir marta yuklanadigan hujjatlar soni"
        )

    def handle(self, *args, **options):
        try:
            from ai_engine.rag import LegalRAG
        except ImportError as e:
            self.stderr.write(self.style.ERROR(f"RAG moduli import qilib bo'lmadi: {e}"))
            return
        
        self.stdout.write("RAG tizimi ishga tushirilmoqda...")
        
        try:
            rag = LegalRAG(
                vector_store_path="./vector_store",
            )
            rag.initialize()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"RAG tizimi ishga tushmadi: {e}"))
            return
        
        if options['clear']:
            self.stdout.write("Avvalgi indekslar tozalanmoqda...")
            try:
                # Clear the collection
                rag.chroma_client.delete_collection("legal_documents")
                rag.collection = rag.chroma_client.get_or_create_collection(
                    name="legal_documents",
                    metadata={"hnsw:space": "cosine"}
                )
                self.stdout.write(self.style.SUCCESS("Indekslar tozalandi"))
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"Tozalashda xatolik: {e}"))
        
        # Get all articles
        articles = LawArticle.objects.select_related('law', 'chapter').all()
        total = articles.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING(
                "Moddalar topilmadi. Avval 'python manage.py load_laws' buyrug'ini ishga tushiring."
            ))
            return
        
        self.stdout.write(f"Jami {total} ta modda indekslanmoqda...")
        
        batch_size = options['batch_size']
        indexed = 0
        
        documents = []
        for article in articles:
            # Prepare document for indexing
            doc = {
                'id': f"article_{article.law.short_name}_{article.number}",
                'text': f"{article.title}\n\n{article.content}",
                'metadata': {
                    'law_id': str(article.law.id),
                    'law_name': article.law.name,
                    'law_short_name': article.law.short_name,
                    'law_type': article.law.law_type,
                    'chapter_number': article.chapter.number if article.chapter else '',
                    'chapter_title': article.chapter.title if article.chapter else '',
                    'article_number': article.number,
                    'article_title': article.title,
                    'is_mandatory': article.is_mandatory,
                    'applies_to': ','.join(article.applies_to) if article.applies_to else '',
                    'keywords': ','.join(article.keywords) if article.keywords else '',
                    'source': 'legal_database',
                }
            }
            documents.append(doc)
            
            # Index in batches
            if len(documents) >= batch_size:
                try:
                    rag.add_documents(documents)
                    indexed += len(documents)
                    self.stdout.write(f"Yuklandi: {indexed}/{total}")
                    documents = []
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Xatolik: {e}"))
        
        # Index remaining documents
        if documents:
            try:
                rag.add_documents(documents)
                indexed += len(documents)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Xatolik: {e}"))
        
        # Update indexed status in database
        LawArticle.objects.all().update(embedding=None)  # Clear old embeddings
        Law.objects.all().update(is_indexed=True)
        
        self.stdout.write(self.style.SUCCESS(
            f"Muvaffaqiyatli yakunlandi! {indexed} ta modda indekslandi."
        ))
        
        # Show collection stats
        try:
            count = rag.collection.count()
            self.stdout.write(f"Vector store da jami: {count} ta hujjat")
        except Exception:
            pass
