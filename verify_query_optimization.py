#!/usr/bin/env python3
"""
Database Query Optimization Verification Script
Analyzes the analytics API for query optimization improvements
"""

import re
from pathlib import Path

def analyze_query_optimization():
    """Analyze the analytics API for query optimization patterns."""
    
    analytics_file = Path("app/api/analytics.py")
    if not analytics_file.exists():
        print("❌ Analytics API file not found")
        return False
    
    content = analytics_file.read_text()
    
    print("🔍 Database Query Optimization Analysis")
    print("=====================================")
    
    # Count different types of queries
    query_patterns = {
        'Single Queries': r'db\.query\([^)]+\)\.filter\([^)]+\)\.(?:count|scalar|first|all)\(\)',
        'Aggregation Queries': r'func\.(count|sum|avg|min|max)',
        'Conditional Aggregations': r'func\.case\(',
        'Group By Queries': r'\.group_by\(',
        'Subqueries': r'\.subquery\(\)',
        'Joins': r'\.join\(',
        'Complex Filters': r'and_\(|or_\('
    }
    
    query_counts = {}
    for pattern_name, pattern in query_patterns.items():
        matches = re.findall(pattern, content)
        query_counts[pattern_name] = len(matches)
    
    print("\n📊 Query Pattern Analysis")
    print("========================")
    for pattern, count in query_counts.items():
        print(f"   {pattern}: {count}")
    
    # Analyze optimization techniques
    optimization_techniques = {
        'Combined Aggregations': r'func\.sum\(func\.case\(',
        'Single Query Multiple Metrics': r'db\.query\([^)]*func\.[^)]*,[^)]*func\.',
        'Date Grouping': r'func\.date\(|func\.extract\(',
        'Conditional Sums': r'func\.sum\(func\.case\(\[\(',
        'Lookup Dictionaries': r'daily_lookup|weekly_lookup|lookup',
        'Batch Processing': r'for.*in.*stats|for.*in.*metrics'
    }
    
    optimization_counts = {}
    for technique, pattern in optimization_techniques.items():
        matches = re.findall(pattern, content)
        optimization_counts[technique] = len(matches)
    
    print("\n🚀 Optimization Techniques")
    print("=========================")
    for technique, count in optimization_counts.items():
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {technique}: {count}")
    
    # Check for performance anti-patterns
    anti_patterns = {
        'N+1 Queries': r'for.*in.*:\s*db\.query',
        'Separate Count Queries': r'\.count\(\)\s*.*\.count\(\)',
        'Multiple Similar Queries': r'db\.query\(Verification\)\.filter.*\n.*db\.query\(Verification\)\.filter',
        'Unoptimized Loops': r'for i in range\([^)]+\):\s*.*db\.query'
    }
    
    anti_pattern_counts = {}
    for pattern_name, pattern in anti_patterns.items():
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        anti_pattern_counts[pattern_name] = len(matches)
    
    print("\n⚠️ Performance Anti-Patterns")
    print("============================")
    total_anti_patterns = 0
    for pattern, count in anti_pattern_counts.items():
        status = "❌" if count > 0 else "✅"
        print(f"   {status} {pattern}: {count}")
        total_anti_patterns += count
    
    # Estimate query reduction
    print("\n📈 Performance Improvements")
    print("===========================")
    
    # Count function definitions to estimate endpoints
    endpoints = len(re.findall(r'@router\.get\(|@router\.post\(', content))
    
    # Estimate original vs optimized query count
    aggregation_queries = query_counts.get('Aggregation Queries', 0)
    combined_aggregations = optimization_counts.get('Combined Aggregations', 0)
    
    estimated_original_queries = aggregation_queries + (endpoints * 3)  # Rough estimate
    estimated_optimized_queries = aggregation_queries - combined_aggregations + endpoints
    
    query_reduction = max(0, estimated_original_queries - estimated_optimized_queries)
    reduction_percentage = (query_reduction / estimated_original_queries * 100) if estimated_original_queries > 0 else 0
    
    print(f"   Estimated Original Queries: {estimated_original_queries}")
    print(f"   Estimated Optimized Queries: {estimated_optimized_queries}")
    print(f"   Query Reduction: {query_reduction} ({reduction_percentage:.1f}%)")
    
    # Performance score calculation
    optimization_score = sum(1 for count in optimization_counts.values() if count > 0)
    max_optimization_score = len(optimization_counts)
    
    anti_pattern_penalty = min(total_anti_patterns * 10, 50)  # Max 50% penalty
    
    performance_score = ((optimization_score / max_optimization_score) * 100) - anti_pattern_penalty
    performance_score = max(0, min(100, performance_score))
    
    print(f"   Performance Score: {performance_score:.1f}/100")
    
    # Overall assessment
    print("\n🎯 Overall Assessment")
    print("====================")
    
    if performance_score >= 80:
        print("✅ Query optimization: EXCELLENT")
        assessment = True
    elif performance_score >= 60:
        print("⚠️ Query optimization: GOOD")
        assessment = True
    elif performance_score >= 40:
        print("⚠️ Query optimization: ADEQUATE")
        assessment = True
    else:
        print("❌ Query optimization: NEEDS IMPROVEMENT")
        assessment = False
    
    # Recommendations
    print("\n💡 Recommendations")
    print("==================")
    
    if optimization_counts.get('Combined Aggregations', 0) < 3:
        print("   • Combine more aggregation queries")
    
    if optimization_counts.get('Date Grouping', 0) == 0:
        print("   • Use date grouping for time-based queries")
    
    if total_anti_patterns > 0:
        print("   • Eliminate N+1 query patterns")
        print("   • Combine similar queries")
    
    if query_reduction < 5:
        print("   • Look for more query consolidation opportunities")
    
    return assessment

if __name__ == "__main__":
    success = analyze_query_optimization()
    exit(0 if success else 1)