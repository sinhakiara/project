"""Tests for scope_manager module."""

import pytest
from scope_manager import ScopeManager, create_scope_manager


class TestScopeManager:
    """Test ScopeManager class."""
    
    def test_initialization(self):
        """Test ScopeManager initialization."""
        manager = ScopeManager()
        
        assert len(manager.in_scope_patterns) == 0
        assert len(manager.out_of_scope_patterns) == 0
        assert len(manager.in_scope_domains) == 0
        assert len(manager.out_of_scope_domains) == 0
    
    def test_add_in_scope_domain(self):
        """Test adding in-scope domain."""
        manager = ScopeManager()
        manager.add_in_scope('example.com')
        
        assert 'example.com' in manager.in_scope_patterns
        assert 'example.com' in manager.in_scope_domains
    
    def test_add_out_of_scope_domain(self):
        """Test adding out-of-scope domain."""
        manager = ScopeManager()
        manager.add_out_of_scope('admin.example.com')
        
        assert 'admin.example.com' in manager.out_of_scope_patterns
        assert 'admin.example.com' in manager.out_of_scope_domains
    
    def test_exact_domain_match(self):
        """Test exact domain matching."""
        manager = ScopeManager()
        manager.add_in_scope('example.com')
        
        assert manager.is_in_scope('https://example.com') is True
        assert manager.is_in_scope('https://example.com/page') is True
        assert manager.is_in_scope('https://api.example.com') is False
    
    def test_wildcard_subdomain(self):
        """Test wildcard subdomain matching (*.domain.tld)."""
        manager = ScopeManager()
        manager.add_in_scope('*.example.com')
        
        # Should match one level of subdomain
        assert manager.is_in_scope('https://api.example.com') is True
        assert manager.is_in_scope('https://admin.example.com') is True
        assert manager.is_in_scope('https://test.example.com') is True
        
        # Should NOT match the base domain
        assert manager.is_in_scope('https://example.com') is False
        
        # Should NOT match nested subdomains (more than one level)
        assert manager.is_in_scope('https://api.v1.example.com') is False
    
    def test_nested_wildcard(self):
        """Test nested wildcard matching (**.domain.tld)."""
        manager = ScopeManager()
        manager.add_in_scope('**.example.com')
        
        # Should match any level of subdomains
        assert manager.is_in_scope('https://api.example.com') is True
        assert manager.is_in_scope('https://api.v1.example.com') is True
        assert manager.is_in_scope('https://test.api.v1.example.com') is True
        
        # Should NOT match the base domain
        assert manager.is_in_scope('https://example.com') is False
    
    def test_exclusion_priority(self):
        """Test that exclusions take priority over inclusions - CRITICAL TEST."""
        manager = ScopeManager()
        
        # Add wildcard to include all subdomains
        manager.add_in_scope('*.example.com')
        
        # Add specific exclusion
        manager.add_out_of_scope('admin.example.com')
        
        # api.example.com should be IN scope
        assert manager.is_in_scope('https://api.example.com') is True
        
        # admin.example.com should be OUT of scope (exclusion priority)
        assert manager.is_in_scope('https://admin.example.com') is False
        
        # test.example.com should be IN scope
        assert manager.is_in_scope('https://test.example.com') is True
    
    def test_exclusion_priority_with_nested_wildcards(self):
        """Test exclusion priority with nested wildcards."""
        manager = ScopeManager()
        
        # Include all nested subdomains
        manager.add_in_scope('**.example.com')
        
        # Exclude specific pattern
        manager.add_out_of_scope('*.admin.example.com')
        
        # These should be IN scope
        assert manager.is_in_scope('https://api.example.com') is True
        assert manager.is_in_scope('https://api.v1.example.com') is True
        
        # These should be OUT of scope (exclusion priority)
        assert manager.is_in_scope('https://test.admin.example.com') is False
        assert manager.is_in_scope('https://dev.admin.example.com') is False
    
    def test_multiple_patterns(self):
        """Test multiple in-scope and out-of-scope patterns."""
        manager = ScopeManager()
        
        # Add multiple in-scope
        manager.add_in_scope('example.com')
        manager.add_in_scope('*.test.com')
        
        # Add multiple out-of-scope
        manager.add_out_of_scope('admin.example.com')
        manager.add_out_of_scope('private.test.com')
        
        # Test example.com
        assert manager.is_in_scope('https://example.com') is True
        assert manager.is_in_scope('https://admin.example.com') is False
        
        # Test test.com
        assert manager.is_in_scope('https://api.test.com') is True
        assert manager.is_in_scope('https://private.test.com') is False
    
    def test_filter_urls(self):
        """Test URL filtering."""
        manager = ScopeManager()
        manager.add_in_scope('example.com')
        manager.add_out_of_scope('admin.example.com')
        
        urls = [
            'https://example.com',
            'https://example.com/page1',
            'https://admin.example.com',
            'https://external.com',
        ]
        
        filtered = manager.filter_urls(urls)
        
        assert len(filtered) == 2
        assert 'https://example.com' in filtered
        assert 'https://example.com/page1' in filtered
        assert 'https://admin.example.com' not in filtered
        assert 'https://external.com' not in filtered
    
    def test_get_scope_summary(self):
        """Test scope summary."""
        manager = ScopeManager()
        manager.add_in_scope('example.com')
        manager.add_in_scope('*.test.com')
        manager.add_out_of_scope('admin.example.com')
        
        summary = manager.get_scope_summary()
        
        assert summary['in_scope_count'] == 2
        assert summary['out_of_scope_count'] == 1
        assert 'example.com' in summary['in_scope_patterns']
        assert '*.test.com' in summary['in_scope_patterns']
        assert 'admin.example.com' in summary['out_of_scope_patterns']
    
    def test_test_url(self):
        """Test URL testing with detailed information."""
        manager = ScopeManager()
        manager.add_in_scope('*.example.com')
        manager.add_out_of_scope('admin.example.com')
        
        # Test in-scope URL
        result = manager.test_url('https://api.example.com')
        assert result['in_scope'] is True
        assert result['domain'] == 'api.example.com'
        assert len(result['matches_in_scope']) > 0
        
        # Test out-of-scope URL (exclusion)
        result = manager.test_url('https://admin.example.com')
        assert result['in_scope'] is False
        assert result['domain'] == 'admin.example.com'
        assert len(result['matches_out_of_scope']) > 0
        assert result['reason'] == 'EXCLUDED'
    
    def test_no_scope_allows_all(self):
        """Test that no in-scope patterns allows everything."""
        manager = ScopeManager()
        
        # No patterns defined
        assert manager.is_in_scope('https://example.com') is True
        assert manager.is_in_scope('https://anything.com') is True
        
        # Add exclusion
        manager.add_out_of_scope('blocked.com')
        
        # Should still allow others but block the excluded
        assert manager.is_in_scope('https://example.com') is True
        assert manager.is_in_scope('https://blocked.com') is False


class TestCreateScopeManager:
    """Test create_scope_manager helper function."""
    
    def test_create_with_patterns(self):
        """Test creating scope manager with patterns."""
        manager = create_scope_manager(
            in_scope=['example.com', '*.test.com'],
            out_of_scope=['admin.example.com']
        )
        
        assert len(manager.in_scope_patterns) == 2
        assert len(manager.out_of_scope_patterns) == 1
        
        assert manager.is_in_scope('https://example.com') is True
        assert manager.is_in_scope('https://api.test.com') is True
        assert manager.is_in_scope('https://admin.example.com') is False
    
    def test_create_empty(self):
        """Test creating empty scope manager."""
        manager = create_scope_manager()
        
        assert len(manager.in_scope_patterns) == 0
        assert len(manager.out_of_scope_patterns) == 0
