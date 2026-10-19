#!/usr/bin/env python3
"""Regenerate an honest, self-hosted SVG from public GitHub REST API data.
Run from repository root via GitHub Actions; no third-party image providers required.
"""
from pathlib import Path
from xml.sax.saxutils import escape
from collections import Counter
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json, os, sys

USER=os.getenv('PROFILE_USERNAME', 'DaoHao-dev')
TOKEN=os.getenv('GITHUB_TOKEN','')
OUTPUT=Path('assets/github-stats.svg')


def get_json(path):
    url='https://api.github.com'+path
    headers={'Accept':'application/vnd.github+json','User-Agent':'DaoHao-dev-profile-action','X-GitHub-Api-Version':'2022-11-28'}
    if TOKEN: headers['Authorization']='Bearer '+TOKEN
    with urlopen(Request(url,headers=headers),timeout=20) as f:
        return json.load(f)


def num(n):
    if isinstance(n,str): return n
    return f'{n:,}'


def build_svg(user='DaoHao-dev',stats=None):
    stats=stats or {}
    placeholders=not bool(stats)
    vals=[stats.get('repos','—'),stats.get('followers','—'),stats.get('stars','—'),stats.get('following','—')]
    labels=['PUBLIC REPOS','FOLLOWERS','STARS RECEIVED','FOLLOWING']
    card=[]
    for i,(v,label) in enumerate(zip(vals,labels)):
        x=30+i*255
        card.append(f'<rect x="{x}" y="69" width="239" height="111" rx="10" fill="#161b22" stroke="#30363d"/>')
        card.append(f'<text x="{x+18}" y="101" font-size="13" font-family="Arial,sans-serif" fill="#8b949e" letter-spacing="1">{label}</text>')
        card.append(f'<text x="{x+18}" y="151" font-size="37" font-family="Arial,sans-serif" font-weight="bold" fill="#f0f6fc">{num(v)}</text>')
    languages=stats.get('languages') or []
    if languages:
        total=sum(c for n,c in languages)
        runs=[]
        x=30
        cols=['#eeeeee','#babfc7','#858e98','#555f6a','#353c45']
        for i,(n,c) in enumerate(languages[:5]):
            w=1000*(c/total)
            runs.append(f'<rect x="{x:.1f}" y="228" width="{w:.1f}" height="9" rx="2" fill="{cols[i]}"/>')
            x+=w
        legend='  ·  '.join(f'{escape(n)} ({c})' for n,c in languages[:5])
        label='PRIMARY LANGUAGES BY PUBLIC REPOSITORY COUNT'
        detail=legend
    else:
        runs=['<rect x="30" y="228" width="1000" height="9" rx="2" fill="#30363d"/>']
        label='PRIMARY LANGUAGES BY PUBLIC REPOSITORY COUNT'
        detail='Run Actions → Update profile visuals → Run workflow to load real statistics' if placeholders else 'No public-repository language data available'
    source='Public GitHub API data · Updated by repository Action' if not placeholders else 'Starter card — waiting for first successful Action run'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="299" viewBox="0 0 1060 299" role="img" aria-label="DaoHao-dev public GitHub statistics">
    <rect width="1060" height="299" rx="18" fill="#0d1117"/>
    <rect x="1" y="1" width="1058" height="297" rx="17" fill="none" stroke="#30363d"/>
    <text x="30" y="42" font-family="Arial,sans-serif" font-size="18" font-weight="bold" letter-spacing="1" fill="#f0f6fc">PUBLIC GITHUB SNAPSHOT</text>
    <text x="1030" y="42" text-anchor="end" font-family="monospace" font-size="13" fill="#9da7b2">@{escape(user)}</text>
    {''.join(card)}
    <text x="30" y="212" font-family="Arial,sans-serif" font-size="12" letter-spacing="1" fill="#9da7b2">{label}</text>
    {''.join(runs)}
    <text x="30" y="255" font-family="Arial,sans-serif" font-size="13" fill="#c0c7d0">{escape(detail[:150])}</text>
    <text x="30" y="280" font-family="monospace" font-size="12" fill="#7d8590">{source}</text>
    </svg>"""


def main():
    try:
        user = get_json('/users/'+USER)
        if user.get('message') == 'Not Found':
            print('User not found; keeping starter image',file=sys.stderr)
            return 1
        if user.get('type')!='User':
            print('Expected a public user account; keeping starter image',file=sys.stderr)
            return 1
        repos=[]
        for page in range(1,11):
            batch=get_json(f'/users/{USER}/repos?per_page=100&page={page}&type=owner')
            if not batch: break
            repos.extend(batch)
            if len(batch)<100:break
        # Restrict languages to non-fork original repos. No fake total contributions.
        langs=Counter((r.get('language') or '').strip() for r in repos if not r.get('fork') and r.get('language'))
        stats={
            'repos':user.get('public_repos',0),
            'followers':user.get('followers',0),
            'following':user.get('following',0),
            'stars':sum(r.get('stargazers_count',0) for r in repos),
            'languages':langs.most_common(5),
        }
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        OUTPUT.write_text(build_svg(USER,stats),encoding='utf8')
        print('Updated',OUTPUT, 'using public GitHub API:',stats)
        return 0
    except (HTTPError,URLError,TimeoutError,ValueError,KeyError) as e:
        print('Could not fetch GitHub public stats; preserving starter image:',str(e),file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
