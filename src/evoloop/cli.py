"""
EvoLoop Command Line Interface.

Provides commands for:
- evoloop ui: Launch the Streamlit trace viewer
- evoloop stats: Show annotation statistics
- evoloop export: Export traces/annotations

Example:
    $ evoloop ui
    $ evoloop ui --port 8502 --db-path my_traces.db
    $ evoloop stats
    $ evoloop export traces --format csv --output traces.csv
"""

import argparse
import sys
from pathlib import Path


def cmd_ui(args):
    """Launch the Streamlit UI."""
    try:
        from evoloop.ui import launch, HAS_STREAMLIT
        
        if not HAS_STREAMLIT:
            print("Error: Streamlit is required for the UI.")
            print("Install it with: pip install evoloop[ui]")
            sys.exit(1)
        
        print(f"🔄 Launching EvoLoop UI on port {args.port}...")
        print(f"   Database: {args.db_path}")
        print(f"   Open: http://localhost:{args.port}")
        print()
        
        launch(port=args.port, db_path=args.db_path)
    except ImportError as e:
        print(f"Error: {e}")
        print("Install the UI dependencies with: pip install evoloop[ui]")
        sys.exit(1)


def cmd_stats(args):
    """Show annotation statistics."""
    from evoloop.storage import SQLiteStorage
    from evoloop.annotations import AnnotationStorage
    
    trace_storage = SQLiteStorage(args.db_path)
    annotation_storage = AnnotationStorage(args.db_path)
    
    # Trace stats
    total_traces = trace_storage.count()
    error_traces = trace_storage.count(status="error")
    success_traces = trace_storage.count(status="success")
    
    print("\n📊 EvoLoop Statistics")
    print("=" * 50)
    print(f"\n📋 Traces:")
    print(f"   Total:   {total_traces}")
    print(f"   Success: {success_traces}")
    print(f"   Error:   {error_traces}")
    
    # Annotation stats
    stats = annotation_storage.get_stats()
    
    if stats.get("total", 0) > 0:
        print(f"\n✏️ Annotations:")
        print(f"   Total:     {stats.get('total', 0)}")
        print(f"   Pass:      {stats.get('pass', 0)}")
        print(f"   Fail:      {stats.get('fail', 0)}")
        print(f"   Skip:      {stats.get('skip', 0)}")
        print(f"   Pass Rate: {stats.get('pass_rate', 0):.1f}%")
        
        taxonomy = stats.get("failure_taxonomy", {})
        if taxonomy:
            print(f"\n🏷️ Failure Taxonomy:")
            for tag, count in list(taxonomy.items())[:10]:
                print(f"   {tag}: {count}")
    else:
        print(f"\n✏️ Annotations: None yet")
    
    # Unannotated count
    unannotated = annotation_storage.get_unannotated_traces(limit=10000)
    print(f"\n⏳ Unannotated traces: {len(unannotated)}")
    
    print()


def cmd_export(args):
    """Export traces or annotations."""
    from evoloop.storage import SQLiteStorage
    from evoloop.annotations import AnnotationStorage
    from evoloop.export import (
        export_traces_to_csv,
        export_traces_to_json,
        export_annotations_to_csv,
        export_annotations_to_json,
    )
    from evoloop.export.json_export import export_for_judge_training
    
    trace_storage = SQLiteStorage(args.db_path)
    annotation_storage = AnnotationStorage(args.db_path)
    
    output = args.output
    fmt = args.format.lower()
    
    if args.what == "traces":
        if fmt == "csv":
            count = export_traces_to_csv(output, trace_storage, limit=args.limit)
        else:
            count = export_traces_to_json(output, trace_storage, limit=args.limit)
        print(f"✅ Exported {count} traces to {output}")
    
    elif args.what == "annotations":
        if fmt == "csv":
            count = export_annotations_to_csv(
                output, annotation_storage,
                limit=args.limit,
                include_trace_data=args.include_traces,
                trace_storage=trace_storage if args.include_traces else None,
            )
        else:
            count = export_annotations_to_json(
                output, annotation_storage,
                limit=args.limit,
                include_trace_data=args.include_traces,
                trace_storage=trace_storage if args.include_traces else None,
            )
        print(f"✅ Exported {count} annotations to {output}")
    
    elif args.what == "judge":
        count = export_for_judge_training(output, annotation_storage, trace_storage, limit=args.limit)
        print(f"✅ Exported {count} examples for judge training to {output}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="evoloop",
        description="EvoLoop - Self-Evolving Agent Framework",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.3.0",
    )
    parser.add_argument(
        "--db-path",
        default="evoloop.db",
        help="Path to SQLite database (default: evoloop.db)",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Launch the Streamlit UI")
    ui_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the UI on (default: 8501)",
    )
    ui_parser.set_defaults(func=cmd_ui)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_stats)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument(
        "what",
        choices=["traces", "annotations", "judge"],
        help="What to export",
    )
    export_parser.add_argument(
        "--format", "-f",
        choices=["csv", "json"],
        default="json",
        help="Export format (default: json)",
    )
    export_parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output file path",
    )
    export_parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Maximum items to export (default: 10000)",
    )
    export_parser.add_argument(
        "--include-traces",
        action="store_true",
        help="Include trace data in annotations export",
    )
    export_parser.set_defaults(func=cmd_export)
    
    # Parse and execute
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
