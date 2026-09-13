"""Command-line entry points for each stage and the complete pipeline."""

import argparse
import sys
from pathlib import Path

from orderscribe.codex import CodexExtractionError, CodexExtractor
from orderscribe.pdf import pdf_to_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PDF → Markdown → Pydantic purchase order")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("convert", "Convert a PDF to Markdown locally"),
        ("extract", "Extract a purchase order from Markdown using Codex"),
        ("run", "Convert a PDF and extract a purchase order using Codex"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("source", type=Path)
        command.add_argument("--output-dir", type=Path, default=Path("output"))
        command.add_argument("--force", action="store_true", help="Replace existing output files")
        if name != "convert":
            command.add_argument("--model", help="Codex model (default: your CLI configuration)")
            command.add_argument(
                "--timeout", type=float, default=180, help="Codex timeout in seconds"
            )
    args = parser.parse_args(argv)
    markdown_path = args.output_dir / f"{args.source.stem}.md"
    json_path = args.output_dir / f"{args.source.stem}.json"
    destinations = []
    if args.command in {"convert", "run"}:
        destinations.append(markdown_path)
    if args.command in {"extract", "run"}:
        destinations.append(json_path)
    try:
        if not args.source.is_file():
            raise FileNotFoundError(f"Input file does not exist: {args.source}")
        for destination in destinations:
            if destination.resolve() == args.source.resolve():
                raise ValueError("Output path must differ from the input path")
            if destination.exists() and not args.force:
                raise FileExistsError(f"Output exists: {destination}. Use --force to replace it.")
        if args.command == "extract":
            if args.source.suffix.lower() != ".md":
                raise ValueError("extract expects a .md file")
            markdown = args.source.read_text(encoding="utf-8")
        else:
            markdown = pdf_to_markdown(args.source)
            args.output_dir.mkdir(parents=True, exist_ok=True)
            markdown_path.write_text(markdown, encoding="utf-8")
            print(f"Markdown: {markdown_path}")
        if args.command != "convert":
            order = CodexExtractor(model=args.model, timeout=args.timeout).extract(markdown)
            args.output_dir.mkdir(parents=True, exist_ok=True)
            json_path.write_text(order.model_dump_json(indent=2) + "\n", encoding="utf-8")
            print(f"Order: {json_path} ({len(order.items)} items)")
        return 0
    except (OSError, ValueError, CodexExtractionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
