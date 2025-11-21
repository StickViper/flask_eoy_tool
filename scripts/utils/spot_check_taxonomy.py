import pandas as pd
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Spot check taxonomy codes in filtered CSV')
    parser.add_argument('input_file', help='Path to the filtered CSV file')
    parser.add_argument('--sample-size', type=int, default=30, help='Number of rows to sample')
    args = parser.parse_args()

    try:
        df = pd.read_csv(args.input_file)
    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)

    # Defensive checks
    required_cols = ['Provider First Name', 'Provider Last Name (Legal Name)', 'City', 'State', 'Healthcare Provider Taxonomy Code_1']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {', '.join(missing_cols)}")
        print(f"Available columns: {', '.join(df.columns)}")
        sys.exit(1)

    print(f'Total providers: {len(df)}')
    if 'State' in df.columns:
        print(f'\nState breakdown:')
        print(df['State'].value_counts())

    print(f'\n{"="*80}')
    print(f'SPOT-CHECK: Random sample of {args.sample_size} providers')
    print(f'{"="*80}\n')

    # Use random sample instead of head
    sample_size = min(args.sample_size, len(df))
    sample = df.sample(n=sample_size)

    for idx, row in sample.iterrows():
        name = f"{row.get('Provider First Name', '')} {row.get('Provider Last Name (Legal Name)', '')}"
        location = f"{row.get('City', '')}, {row.get('State', '')}"

        print(f"{idx+1}. {name} - {location}")
        print(f"   Taxonomy 1: {row.get('Healthcare Provider Taxonomy Code_1', 'N/A')}")
        
        if 'Healthcare Provider Taxonomy Code_2' in row and pd.notna(row['Healthcare Provider Taxonomy Code_2']):
            print(f"   Taxonomy 2: {row['Healthcare Provider Taxonomy Code_2']}")
        if 'Healthcare Provider Taxonomy Code_3' in row and pd.notna(row['Healthcare Provider Taxonomy Code_3']):
            print(f"   Taxonomy 3: {row['Healthcare Provider Taxonomy Code_3']}")
        print()

if __name__ == "__main__":
    main()
