#!/usr/bin/env python3
"""NEXUS-0: radar exploratorio de recompensas GitHub; no confirma ni cobra premios."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com"
QUERIES = ("is:issue is:open label:bounty", 'is:issue is:open "bounty" "$"')
MONEY = r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)"
AFTER = re.compile(r"(?:bounty|reward|pays|prize|recompensa)[^\n\r]{0,35}?" + MONEY, re.I)
BEFORE = re.compile(MONEY + r"[^\n\r]{0,22}?(?:bounty|reward|prize)", re.I)
TITLE = re.compile(r"^\s*\[\s*" + MONEY + r"\s*\]", re.I)
ATTEMPT = re.compile(r"(?:^|\s)/(?:attempt|claim|opire\s+try)\b|\b(?:opened|submitted|implemented)\s+(?:pr|pull request)\b", re.I)
PR_LINK = re.compile(r"github\.com/[\w.-]+/[\w.-]+/pull/\d+", re.I)

def fetch(url: str, token: str | None = None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "nexus-radar/0.2",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))

def parse_amount(text: str | None) -> float | None:
    if not text:
        return None
    values = []
    for regex in (TITLE, AFTER, BEFORE):
        for match in regex.finditer(text):
            try:
                n = float(match.group(1).replace(",", ""))
                if 1 <= n <= 100000:
                    values.append(n)
            except ValueError:
                continue
    return max(values, default=None)

def find_existing_prs(issue: dict, pull_requests: list[dict] | None):
    """Busca referencias exactas a #numero en PR recientes del mismo repositorio.

    Esto es una señal de competencia, NO prueba de que la tarea esté resuelta.
    None indica falta de comprobación; [] indica que los PR recuperados no
    contienen una referencia identificable. Solo se revisa una página reciente.
    """
    if pull_requests is None:
        return None
    issue_number = int(issue["number"])
    reference = re.compile(r"(?<!\w)#" + str(issue_number) + r"\b")
    found = []
    for pr in pull_requests:
        combined = str(pr.get("title") or "") + "\n" + str(pr.get("body") or "")
        if reference.search(combined):
            found.append({
                "url": pr.get("html_url"),
                "numero": pr.get("number"),
                "estado": pr.get("state"),
                "fusionada": bool(pr.get("merged_at")),
            })
    return found


def evaluate(issue: dict, comments: list[dict], now: dt.datetime, min_amount=30, max_days=35, pull_requests: list[dict] | None = None):
    if issue.get("state") != "open" or "pull_request" in issue:
        return None
    required = ("title", "updated_at", "repository_url", "number", "html_url")
    if not all(k in issue for k in required):
        return None
    age = (now - parse_utc(issue["updated_at"])).total_seconds() / 86400
    if age < -1 or age > max_days:
        return None
    amount = parse_amount(issue["title"])
    source = "titulo"
    if amount is None:
        amount = parse_amount((issue.get("body") or "")[:1600])
        source = "descripcion"
    if amount is None or amount < min_amount:
        return None
    labels = [str(x.get("name", "")) for x in issue.get("labels") or []]
    if any(re.search(r"\b(paid|closed-bounty|rewarded|invalid|not-planned)\b", x, re.I) for x in labels):
        return None
    attempts = sum(bool(ATTEMPT.search(x.get("body") or "") or PR_LINK.search(x.get("body") or "")) for x in comments)
    risks = ["monto anunciado; pago, financiacion y elegibilidad NO verificados"]
    if attempts:
        risks.append(str(attempts) + " comentarios con intentos o pull requests")
    if issue.get("assignee") or issue.get("assignees"):
        risks.append("responsables asignados")
    if (issue.get("comments") or 0) >= 20:
        risks.append("competencia potencial: muchos comentarios")
    if age > 10:
        risks.append("sin actualizacion reciente")
    linked_prs = find_existing_prs(issue, pull_requests)
    if linked_prs is None:
        risks.append("PR externos no comprobados")
    elif linked_prs:
        risks.append(str(len(linked_prs)) + " PR recientes mencionan esta incidencia")

    return {
        "repositorio": issue["repository_url"].split("/repos/")[-1],
        "numero": issue["number"],
        "titulo": issue["title"],
        "url": issue["html_url"],
        "recompensa_anunciada_usd": amount,
        "fuente_importe": source,
        "actualizado_hace_dias": round(age, 1),
        "intentos_detectados": attempts,
        "pull_requests_relacionados": linked_prs,
        "comprobacion_pr_limitada": "solo los 100 PR actualizados recientemente",
        "advertencias": risks,
        "estado": "candidato para revision manual; NO premio garantizado",
    }

def scan(token: str | None = None, limit=12, min_amount=30, max_days=35):
    now = dt.datetime.now(dt.timezone.utc)
    issues = {}
    for query in QUERIES:
        params = urllib.parse.urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": limit})
        for issue in fetch(API + "/search/issues?" + params, token).get("items", []):
            if issue.get("id"):
                issues[issue["id"]] = issue
        time.sleep(0.3)
    candidates = []
    pull_cache = {}
    for issue in issues.values():
        if evaluate(issue, [], now, min_amount, max_days) is None:
            continue
        comments = []
        if issue.get("comments"):
            try:
                comments = fetch(issue["comments_url"] + "?per_page=100", token)
                time.sleep(0.15)
            except (OSError, ValueError):
                pass
        repo = issue["repository_url"].split("/repos/")[-1]
        if repo not in pull_cache and len(pull_cache) < 12:
            endpoint = API + "/repos/" + repo + "/pulls?state=all&sort=updated&direction=desc&per_page=100"
            try:
                response = fetch(endpoint, token)
                pull_cache[repo] = response if isinstance(response, list) else None
            except (OSError, ValueError):
                pull_cache[repo] = None
            time.sleep(0.15)
        record = evaluate(issue, comments, now, min_amount, max_days, pull_requests=pull_cache.get(repo))
        if record:
            candidates.append(record)
    candidates.sort(key=lambda x: (bool(x["pull_requests_relacionados"]), x["intentos_detectados"] > 0, len(x["advertencias"]), -x["recompensa_anunciada_usd"]))
    return candidates

def save_report(candidates: list[dict], destination: Path):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = {"generado_utc": now, "advertencia": "Financiacion, pagador, elegibilidad y pagos NO verificados.", "candidatos": candidates}
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# NEXUS - Radar exploratorio", "", "Fecha UTC: " + now, "", "**NINGUN resultado garantiza pago ni acredita financiacion.**", ""]
    if not candidates:
        lines.append("Sin candidatos con los filtros actuales; pueden existir otras recompensas.")
    for x in candidates:
        lines.extend(["## USD " + str(x["recompensa_anunciada_usd"]) + " — " + x["repositorio"] + "#" + str(x["numero"]), "[" + x["titulo"] + "](" + x["url"] + ")", "Advertencias: " + "; ".join(x["advertencias"]), ""])
        for pr in (x["pull_requests_relacionados"] or []):
            if pr["url"]:
                lines.append("- PR relacionado: " + pr["url"])
        lines.append("")
    destination.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-usd", type=float, default=30)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--max-days", type=int, default=35)
    parser.add_argument("--output", default="reports/resultados_nexus.json")
    args = parser.parse_args()
    try:
        results = scan(os.getenv("GITHUB_TOKEN"), max(1, min(args.limit, 30)), args.min_usd, args.max_days)
        save_report(results, Path(args.output))
        print(str(len(results)) + " candidatos: " + args.output)
    except (OSError, ValueError, KeyError) as exc:
        print("NEXUS fallo: " + str(exc), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
