"""
Serializers for Contracts app.
"""

from rest_framework import serializers
from .models import Contract, ContractSection, ContractClause, ContractVersion, ContractComment


class ContractClauseSerializer(serializers.ModelSerializer):
    """Serializer for contract clauses."""
    
    class Meta:
        model = ContractClause
        fields = [
            'id', 'clause_number', 'content', 'is_standard', 'is_one_sided',
            'is_risky', 'risk_description', 'related_law', 'law_article', 'order'
        ]
        read_only_fields = ['id']


class ContractSectionSerializer(serializers.ModelSerializer):
    """Serializer for contract sections."""
    
    clauses = ContractClauseSerializer(many=True, read_only=True)
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    
    class Meta:
        model = ContractSection
        fields = [
            'id', 'section_type', 'section_type_display', 'section_number',
            'title', 'content', 'order', 'is_compliant', 'risk_level',
            'issues', 'suggestions', 'clauses'
        ]
        read_only_fields = ['id']


class ContractVersionSerializer(serializers.ModelSerializer):
    """Serializer for contract versions."""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ContractVersion
        fields = [
            'id', 'version_number', 'file', 'changes_description',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ContractCommentSerializer(serializers.ModelSerializer):
    """Serializer for contract comments."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = ContractComment
        fields = [
            'id', 'contract', 'section', 'user', 'user_name', 'content',
            'is_resolved', 'resolved_by', 'resolved_by_name', 'resolved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ContractListSerializer(serializers.ModelSerializer):
    """Serializer for contract list view."""
    
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    risk_score = serializers.SerializerMethodField()
    counterparty = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'title', 'original_filename',
            'contract_type', 'contract_type_display', 'language',
            'party_a', 'party_b', 'counterparty', 'contract_date', 'total_amount', 'currency',
            'status', 'status_display', 'uploaded_by', 'uploaded_by_name',
            'assigned_to', 'assigned_to_name', 'comments_count', 'risk_score',
            'created_at', 'analyzed_at'
        ]
    
    def get_risk_score(self, obj):
        """Get risk score from latest analysis."""
        latest_analysis = obj.analyses.filter(status='completed').order_by('-created_at').first()
        if latest_analysis:
            return latest_analysis.overall_score
        return None
    
    def get_counterparty(self, obj):
        """Get counterparty name (party_b or party_a if party_b is empty)."""
        return obj.party_b if obj.party_b else obj.party_a


class ContractDetailSerializer(serializers.ModelSerializer):
    """Serializer for contract detail view."""
    
    sections = ContractSectionSerializer(many=True, read_only=True)
    versions = ContractVersionSerializer(many=True, read_only=True)
    comments = ContractCommentSerializer(many=True, read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    
    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'original_file', 'original_filename',
            'file_type', 'file_size', 'extracted_text', 'is_scanned', 'ocr_confidence',
            'title', 'contract_type', 'contract_type_display', 'language', 'language_display',
            'party_a', 'party_a_inn', 'party_b', 'party_b_inn',
            'contract_date', 'start_date', 'end_date',
            'total_amount', 'currency', 'status', 'status_display',
            'uploaded_by', 'uploaded_by_name', 'assigned_to', 'assigned_to_name',
            'notes', 'created_at', 'updated_at', 'analyzed_at',
            'sections', 'versions', 'comments'
        ]
        read_only_fields = [
            'id', 'extracted_text', 'is_scanned', 'ocr_confidence',
            'uploaded_by', 'created_at', 'updated_at', 'analyzed_at'
        ]


class ContractUploadSerializer(serializers.ModelSerializer):
    """Serializer for contract upload."""
    
    class Meta:
        model = Contract
        fields = [
            'id', 'original_file', 'title', 'contract_type', 'notes', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']
    
    def validate_original_file(self, value):
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'image/jpeg', 'image/png', 'image/tiff']
        
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            raise serializers.ValidationError(
                'Faqat PDF, Word va rasm fayllari qabul qilinadi'
            )
        
        # Validate file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                'Fayl hajmi 10MB dan oshmasligi kerak'
            )
        
        return value
    
    def create(self, validated_data):
        file = validated_data['original_file']
        validated_data['original_filename'] = file.name
        validated_data['file_type'] = file.name.split('.')[-1].lower()
        validated_data['file_size'] = file.size
        validated_data['uploaded_by'] = self.context['request'].user
        
        return super().create(validated_data)


class ContractUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating contract."""
    
    class Meta:
        model = Contract
        fields = [
            'contract_number', 'title', 'contract_type', 'language',
            'party_a', 'party_a_inn', 'party_b', 'party_b_inn',
            'contract_date', 'start_date', 'end_date',
            'total_amount', 'currency', 'assigned_to', 'notes'
        ]


class ContractStatusSerializer(serializers.Serializer):
    """Serializer for changing contract status."""
    
    status = serializers.ChoiceField(choices=Contract.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
