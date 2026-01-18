"""Multiple export formats for StealthCrawler v17/v18 with God Mode compatibility."""

import json
import csv
import logging
from typing import List, Any
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def export_results(results: List[Any], output_path: str, format: str = 'json') -> bool:
    """
    Export crawl results in various formats.

    Args:
        results: List of crawl results
        output_path: Output file path
        format: Export format (json, csv, xml, html)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            return export_json(results, output_path)
        elif format == 'csv':
            return export_csv(results, output_path)
        elif format == 'xml':
            return export_xml(results, output_path)
        elif format == 'html':
            return export_html(results, output_path)
        else:
            logger.error(f"Unknown export format: {format}")
            return False

    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False

def export_json(results: List[Any], output_path: str) -> bool:
    """Export results as JSON."""
    try:
        # Convert results to dicts
        data = []
        for result in results:
            if hasattr(result, 'to_dict'):
                data.append(result.to_dict())
            else:
                data.append(result)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'exported_at': datetime.utcnow().isoformat(),
                    'total_results': len(data),
                    'format': 'json'
                },
                'results': data
            }, f, indent=2, default=str)

        logger.info(f"Exported {len(data)} results to JSON: {output_path}")
        return True

    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        return False

def export_csv(results: List[Any], output_path: str) -> bool:
    """Export results as CSV."""
    try:
        if not results:
            logger.warning("No results to export")
            return False

        # Convert results to dicts
        data = []
        for result in results:
            if hasattr(result, 'to_dict'):
                data.append(result.to_dict())
            else:
                data.append(result)

        # Get all unique keys
        keys = set()
        for item in data:
            keys.update(item.keys())

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            for item in data:
                # Flatten nested structures
                flat_item = {}
                for key, value in item.items():
                    if isinstance(value, (list, dict)):
                        flat_item[key] = json.dumps(value)
                    else:
                        flat_item[key] = value
                writer.writerow(flat_item)

        logger.info(f"Exported {len(data)} results to CSV: {output_path}")
        return True

    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        return False

def export_xml(results: List[Any], output_path: str) -> bool:
    """Export results as XML."""
    try:
        root = ET.Element('crawl_results')
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'exported_at').text = datetime.utcnow().isoformat()
        ET.SubElement(metadata, 'total_results').text = str(len(results))
        results_elem = ET.SubElement(root, 'results')

        for result in results:
            if hasattr(result, 'to_dict'):
                data = result.to_dict()
            else:
                data = result
            result_elem = ET.SubElement(results_elem, 'result')
            for key, value in data.items():
                elem = ET.SubElement(result_elem, key)
                if isinstance(value, (list, dict)):
                    elem.text = json.dumps(value)
                else:
                    elem.text = str(value) if value is not None else ''

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        logger.info(f"Exported {len(results)} results to XML: {output_path}")
        return True

    except Exception as e:
        logger.error(f"XML export failed: {e}")
        return False

def export_html(results: List[Any], output_path: str) -> bool:
    """Export results as HTML report."""
    try:
        data = []
        for result in results:
            if hasattr(result, 'to_dict'):
                data.append(result.to_dict())
            else:
                data.append(result)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StealthCrawler Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        .metadata {{
            background: white;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .success {{
            color: green;
            font-weight: bold;
        }}
        .error {{
            color: red;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>StealthCrawler - Crawl Results</h1>

    <div class="metadata">
        <p><strong>Exported:</strong> {datetime.utcnow().isoformat()}</p>
        <p><strong>Total Results:</strong> {len(data)}</p>
        <p><strong>Successful:</strong> {sum(1 for r in data if r.get('success'))}</p>
        <p><strong>Failed:</strong> {sum(1 for r in data if not r.get('success'))}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>URL</th>
                <th>Status</th>
                <th>Title</th>
                <th>Depth</th>
                <th>Links</th>
                <th>Timestamp</th>
            </tr>
        </thead>
        <tbody>
"""

        for item in data:
            status_class = 'success' if item.get('success') else 'error'
            html += f"""
            <tr>
                <td><a href="{item.get('url', '')}" target="_blank">{item.get('url', '')[:80]}</a></td>
                <td class="{status_class}">{item.get('status', 'N/A')}</td>
                <td>{item.get('title', 'N/A')[:50]}</td>
                <td>{item.get('depth', 'N/A')}</td>
                <td>{len(item.get('links', []))}</td>
                <td>{item.get('timestamp', 'N/A')[:19]}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"Exported {len(data)} results to HTML: {output_path}")
        return True

    except Exception as e:
        logger.error(f"HTML export failed: {e}")
        return False

# === GOD MODE/MAIN.PY COMPATIBLE EXPORTER CLASS ===
class Exporters:
    """
    Unified exporters interface for God Mode crawler and for backward compatibility.

    Usage:
        Exporters.write(results, path, mode='json')
    """
    formats = {
        "json": export_json,
        "csv": export_csv,
        "xml": export_xml,
        "html": export_html
    }

    @classmethod
    def write(cls, results, path, mode="json"):
        mode = mode.lower()
        # If results is Dict (main.py), convert to list for these functions:
        if isinstance(results, dict):
            result_list = list(results.values())
        else:
            result_list = results
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        func = cls.formats.get(mode)
        if not func:
            raise ValueError(f"Unknown export format: {mode}")
        func(result_list, path)
