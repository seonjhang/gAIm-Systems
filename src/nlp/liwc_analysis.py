"""
LIWC (Linguistic Inquiry and Word Count) Analysis
Analyzes player interview transcripts for psychological and linguistic features
"""

import pandas as pd
import numpy as np
import re
import os
from collections import Counter
import csv

# Import full LIWC dictionary
from .liwc_dictionary import LIWC_CATEGORIES

# For backward compatibility, keep simplified structure for reference
OLD_CATEGORIES = {
    'emotional': {
        'positive_emotion': ['happy', 'joy', 'love', 'laugh', 'smile', 'great', 'good', 'excellent', 'awesome', 'fantastic', 'wonderful'],
        'negative_emotion': ['sad', 'angry', 'hate', 'fear', 'worry', 'anxiety', 'stress', 'bad', 'terrible', 'awful', 'frustrated'],
        'anxiety': ['worried', 'anxious', 'nervous', 'afraid', 'fear', 'panic', 'stress', 'pressure'],
        'anger': ['angry', 'mad', 'frustrated', 'annoyed', 'pissed', 'rage', 'upset']
    },
    'cognitive': {
        'insight': ['think', 'thought', 'know', 'understand', 'realize', 'realize', 'consider', 'insight'],
        'cause': ['because', 'effect', 'reason', 'why', 'since', 'therefore', 'due to'],
        'certainty': ['always', 'never', 'definitely', 'certain', 'sure', 'absolute'],
        'doubt': ['maybe', 'perhaps', 'might', 'could', 'uncertain', 'unsure']
    },
    'social': {
        'family': ['mother', 'father', 'mom', 'dad', 'parent', 'brother', 'sister', 'family'],
        'friend': ['friend', 'buddy', 'pal', 'teammate', 'friend'],
        'team': ['team', 'teammate', 'coach', 'player', 'guys', 'squad', 'group']
    },
    'other': {
        'first_person_singular': ['I', 'me', 'my', 'myself', 'mine'],
        'first_person_plural': ['we', 'us', 'our', 'ours', 'ourselves'],
        'second_person': ['you', 'your', 'yours', 'yourself', 'yourselves'],
        'third_person': ['he', 'she', 'they', 'him', 'her', 'them', 'his', 'their'],
        'articles': ['a', 'an', 'the'],
        'prepositions': ['in', 'on', 'at', 'for', 'with', 'by', 'from', 'to', 'of', 'about', 'into', 'onto']
    }
}

def calculate_liwc_scores(text):
    """
    Calculate LIWC scores for a given text.
    Returns a dictionary with category percentages.
    """
    if not text or pd.isna(text):
        return {}
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    total_words = len(words)
    
    if total_words == 0:
        return {}
    
    scores = {}
    
    # Calculate scores for each category (flat structure in new dictionary)
    for category_name, category_words in LIWC_CATEGORIES.items():
        count = sum(1 for word in words if word in category_words)
        percentage = (count / total_words) * 100 if total_words > 0 else 0
        scores[category_name] = percentage
    
    # Additional metrics
    scores['word_count'] = total_words
    scores['avg_sentence_length'] = len(words) / max(text.count('.') + text.count('!') + text.count('?'), 1)
    
    return scores

def analyze_interviews(csv_file='data/asap_hockey_until.csv', output_file='data/liwc_results.csv'):
    """
    Analyze all interviews in the CSV file using LIWC categories.
    
    Args:
        csv_file: Path to input CSV file
        output_file: Path to output CSV file with LIWC results
    """
    # Check if input file exists
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found!")
        return
    
    print(f"Reading data from {csv_file}...")
    # Read CSV with different error handling for multi-line fields
    try:
        df = pd.read_csv(csv_file, quoting=csv.QUOTE_ALL, on_bad_lines='skip')
    except TypeError:
        # Older pandas versions
        df = pd.read_csv(csv_file, quoting=csv.QUOTE_ALL, error_bad_lines=False, warn_bad_lines=False)
    
    print(f"Found {len(df)} interviews to analyze")
    print(f"Columns: {list(df.columns)}")
    
    # Calculate LIWC scores for each interview
    print("\nCalculating LIWC scores...")
    liwc_results = []
    
    for idx, row in df.iterrows():
        player_name = row['player_name']
        transcript = row['transcript_text']
        
        scores = calculate_liwc_scores(transcript)
        
        # Combine original data with LIWC scores
        result = {
            'player_name': player_name,
            'interview_date': row['interview_date'],
            'event_title': row['event_title'],
            'source_url': row['source_url'],
            'word_count': scores.get('word_count', 0),
            **scores
        }
        
        liwc_results.append(result)
        
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{len(df)} interviews...")
    
    # Convert to DataFrame
    results_df = pd.DataFrame(liwc_results)
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    results_df.to_csv(output_file, index=False)
    print(f"\nLIWC analysis complete! Results saved to {output_file}")
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total interviews analyzed: {len(results_df)}")
    print(f"Average word count: {results_df['word_count'].mean():.2f}")
    
    # Top players by positive emotion
    if 'positive_emotion' in results_df.columns:
        print("\n=== Top 10 Players by Positive Emotion ===")
        top_positive = results_df.nlargest(10, 'positive_emotion')[['player_name', 'positive_emotion', 'word_count']]
        for _, row in top_positive.iterrows():
            print(f"{row['player_name']}: {row['positive_emotion']:.2f}% (WC: {int(row['word_count'])})")
    
    # Analyze by emotional patterns
    if 'positive_emotion' in results_df.columns and 'negative_emotion' in results_df.columns:
        print("\n=== Emotional Patterns ===")
        df_with_emotions = results_df[results_df['word_count'] >= 50]  # Only analyze substantial interviews
        
        print(f"\nAverage Positive Emotion: {df_with_emotions['positive_emotion'].mean():.2f}%")
        print(f"Average Negative Emotion: {df_with_emotions['negative_emotion'].mean():.2f}%")
        print(f"Average Anxiety: {df_with_emotions.get('anxiety', pd.Series([0])).mean():.2f}%")
        
        # Emotional ratio
        results_df['emotional_ratio'] = results_df['positive_emotion'] / (results_df['negative_emotion'] + 1)
    
    return results_df

def analyze_player_patterns(results_df, player_name=None):
    """
    Analyze patterns for specific player or all players.
    
    Args:
        results_df: DataFrame with LIWC results
        player_name: Specific player name (optional)
    """
    if player_name:
        player_df = results_df[results_df['player_name'] == player_name]
        if len(player_df) == 0:
            print(f"Player {player_name} not found in results")
            return
        print(f"\n=== Analysis for {player_name} ===")
    else:
        player_df = results_df
        print(f"\n=== Overall Patterns ===")
    
    # Focus on substantial interviews (word count > 50)
    substantial_df = player_df[player_df['word_count'] >= 50]
    
    if len(substantial_df) == 0:
        print("Not enough substantial interviews for analysis")
        return
    
    print(f"\nInterviews analyzed: {len(substantial_df)}")
    print(f"Total words: {substantial_df['word_count'].sum()}")
    print(f"Average interview length: {substantial_df['word_count'].mean():.2f} words")
    
    # Emotional profile
    if 'positive_emotion' in substantial_df.columns:
        print(f"\nPositive Emotion: {substantial_df['positive_emotion'].mean():.2f}%")
        print(f"Negative Emotion: {substantial_df['negative_emotion'].mean():.2f}%")
    
    # Cognitive patterns
    if 'insight' in substantial_df.columns:
        print(f"\nInsight words: {substantial_df['insight'].mean():.2f}%")
        print(f"Causation words: {substantial_df.get('cause', pd.Series([0])).mean():.2f}%")
    
    # First-person usage
    if 'first_person_singular' in substantial_df.columns:
        print(f"\nFirst Person (I/me): {substantial_df['first_person_singular'].mean():.2f}%")
        print(f"First Person (We/us): {substantial_df['first_person_plural'].mean():.2f}%")

if __name__ == "__main__":
    # Run LIWC analysis
    results = analyze_interviews()
    
    # Analyze specific player or all players
    if results is not None and len(results) > 0:
        # Example: analyze all players
        analyze_player_patterns(results)
        
        # Example: analyze specific player
        # analyze_player_patterns(results, "Aamodt, Wyatt")
        
        print("\n=== Analysis Complete ===")
        print("You can load the results CSV to perform further analysis or visualization.")

