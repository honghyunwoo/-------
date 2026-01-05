#!/usr/bin/env python3
"""
Shorts Factory - 유튜브 쇼츠 자동 생성 CLI
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(Path(__file__).parent / 'config' / '.env')

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from core.quote_loader import QuoteLoader, QuoteNotFoundError
from core.script_generator import ScriptGenerator, Script

# Windows 인코딩 문제 해결
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

console = Console(force_terminal=True)

# 기본 경로 설정
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
CONFIG_DIR = BASE_DIR / 'config'
OUTPUT_DIR = BASE_DIR / 'output'
ASSETS_DIR = BASE_DIR / 'assets'


@click.group()
@click.version_option(version='0.2.0')
def cli():
    """
    Shorts Factory - 유튜브 쇼츠 자동 생성 도구

    스토아 철학 명언을 기반으로 유튜브 쇼츠 스크립트와 영상을 자동 생성합니다.

    \b
    주요 명령어:
      - generate: 스크립트만 생성
      - run: 전체 파이프라인 실행 (스크립트 → TTS → 영상)
      - batch: 여러 명언 배치 처리
    """
    pass


@cli.command()
@click.option('--channel', '-c', default='stoic', help='채널 유형 (stoic/english)')
def list_quotes(channel):
    """명언 라이브러리 목록 조회"""
    library_path = TEMPLATES_DIR / channel / 'quotes_library.json'

    try:
        loader = QuoteLoader(library_path)
        quotes = loader.list_all()

        table = Table(title=f"📜 명언 라이브러리 ({channel})")
        table.add_column("ID", style="cyan", width=4)
        table.add_column("저자", style="magenta", width=15)
        table.add_column("명언", style="white", width=50)
        table.add_column("사용", style="green", width=4)

        for q in quotes:
            text = q.text[:47] + "..." if len(q.text) > 50 else q.text
            table.add_row(
                str(q.id),
                q.author,
                text,
                str(q.used_count)
            )

        console.print(table)
        console.print(f"\n총 {len(quotes)}개의 명언")

    except FileNotFoundError as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', default=5, help='표시할 개수')
@click.option('--channel', '-c', default='stoic', help='채널 유형')
def list_unused(channel, limit):
    """사용하지 않은 명언 목록 조회"""
    library_path = TEMPLATES_DIR / channel / 'quotes_library.json'

    try:
        loader = QuoteLoader(library_path)
        unused = loader.get_unused(limit)

        table = Table(title=f"📝 미사용 명언 TOP {limit}")
        table.add_column("ID", style="cyan", width=4)
        table.add_column("저자", style="magenta", width=15)
        table.add_column("명언", style="white", width=50)
        table.add_column("테마", style="yellow", width=20)

        for q in unused:
            text = q.text[:47] + "..." if len(q.text) > 50 else q.text
            themes = ', '.join(q.themes[:3])
            table.add_row(str(q.id), q.author, text, themes)

        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('quote_id', type=int)
@click.option('--channel', '-c', default='stoic', help='채널 유형')
def show_quote(quote_id, channel):
    """특정 명언 상세 조회"""
    library_path = TEMPLATES_DIR / channel / 'quotes_library.json'

    try:
        loader = QuoteLoader(library_path)
        quote = loader.get_by_id(quote_id)

        panel = Panel(
            f"""[bold cyan]명언 #{quote.id}[/bold cyan]

[white]"{quote.text}"[/white]

[magenta]- {quote.author}[/magenta], {quote.source}

[yellow]테마:[/yellow] {', '.join(quote.themes)}
[green]사용 횟수:[/green] {quote.used_count}
[dim]마지막 사용:[/dim] {quote.last_used or '없음'}
""",
            title="📜 명언 상세",
            expand=False
        )
        console.print(panel)

    except QuoteNotFoundError as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('quote_id', type=int)
@click.option('--hook', '-h', default='H1', help='훅 유형 (H1-H5)')
@click.option('--cta', '-t', default='C3', help='CTA 유형 (C1-C5)')
@click.option('--channel', '-c', default='stoic', help='채널 유형')
@click.option('--use-api/--no-api', default=True, help='Claude API 사용 여부')
def generate(quote_id, hook, cta, channel, use_api):
    """스크립트 생성"""
    library_path = TEMPLATES_DIR / channel / 'quotes_library.json'
    prompts_path = TEMPLATES_DIR / channel / 'prompts.yaml'

    try:
        # 명언 로드
        loader = QuoteLoader(library_path)
        quote = loader.get_by_id(quote_id)

        console.print(f"\n[cyan]📜 명언 #{quote.id}:[/cyan] {quote.text[:50]}...")
        console.print(f"[magenta]저자:[/magenta] {quote.author}")
        console.print(f"[yellow]훅:[/yellow] {hook} | [yellow]CTA:[/yellow] {cta}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            if use_api:
                api_key = os.getenv('GOOGLE_API_KEY')
                if not api_key:
                    console.print("[red]오류: GOOGLE_API_KEY가 설정되지 않았습니다.[/red]")
                    console.print("[dim]config/.env 파일에 API 키를 설정하세요.[/dim]")
                    use_api = False

            if use_api:
                task = progress.add_task("스크립트 생성 중...", total=None)
                generator = ScriptGenerator(api_key, prompts_path)
                script = generator.generate(quote, hook, cta)
            else:
                task = progress.add_task("템플릿 기반 스크립트 생성 중...", total=None)
                # API 없이 간단 생성
                generator = ScriptGenerator.__new__(ScriptGenerator)
                script = generator.generate_simple(quote, hook, cta)

            progress.update(task, completed=True)

        # 결과 출력
        console.print(Panel(
            script.full_text,
            title="✨ 생성된 스크립트",
            border_style="green"
        ))

        # 출력 디렉토리 생성
        today = datetime.now().strftime('%Y-%m-%d')
        title_slug = quote.text[:20].replace(' ', '_').replace('"', '')
        output_path = OUTPUT_DIR / f"{today}_{title_slug}"
        output_path.mkdir(parents=True, exist_ok=True)

        # 스크립트 저장
        import json
        script_path = output_path / 'script.json'
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script.to_dict(), f, ensure_ascii=False, indent=2)

        # TTS용 텍스트 저장
        tts_path = output_path / 'tts_text.txt'
        with open(tts_path, 'w', encoding='utf-8') as f:
            f.write(script.get_tts_text())

        console.print(f"\n[green]✅ 스크립트 저장됨:[/green] {script_path}")
        console.print(f"[green]✅ TTS 텍스트 저장됨:[/green] {tts_path}")

        # 명언 사용 표시
        loader.mark_used(quote_id)
        console.print(f"[dim]명언 #{quote_id} 사용 표시 완료[/dim]")

    except QuoteNotFoundError as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--channel', '-c', default='stoic', help='채널 유형')
def stats(channel):
    """명언 라이브러리 통계"""
    library_path = TEMPLATES_DIR / channel / 'quotes_library.json'

    try:
        loader = QuoteLoader(library_path)
        stats = loader.get_stats()

        console.print(Panel(
            f"""[bold cyan]📊 명언 라이브러리 통계[/bold cyan]

[white]총 명언 수:[/white] {stats['total']}개
[green]사용된 명언:[/green] {stats['used']}개
[yellow]미사용 명언:[/yellow] {stats['unused']}개

[bold]저자별 분포:[/bold]
{chr(10).join(f"  • {author}: {count}개" for author, count in stats['by_author'].items())}

[bold]테마별 분포:[/bold]
{chr(10).join(f"  • {theme}: {count}개" for theme, count in list(stats['by_theme'].items())[:10])}
""",
            title=f"📈 {channel.upper()} 채널 통계",
            expand=False
        ))

    except FileNotFoundError as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


@cli.command()
def info():
    """시스템 정보 및 설정 확인"""
    # B-roll 상태 확인
    broll_dir = ASSETS_DIR / 'b-roll'
    broll_count = len(list(broll_dir.glob('**/*.mp4'))) if broll_dir.exists() else 0

    # BGM 상태 확인
    bgm_dir = ASSETS_DIR / 'bgm'
    bgm_count = len(list(bgm_dir.glob('*.mp3'))) if bgm_dir.exists() else 0

    console.print(Panel(
        f"""[bold cyan]Shorts Factory v0.2.0[/bold cyan]

[white]유튜브 쇼츠 자동 생성 도구[/white]

[bold]경로 설정:[/bold]
  • 템플릿: {TEMPLATES_DIR}
  • 설정: {CONFIG_DIR}
  • 출력: {OUTPUT_DIR}
  • 에셋: {ASSETS_DIR}

[bold]API 키 상태:[/bold]
  • GOOGLE_API_KEY: {'✅ 설정됨' if os.getenv('GOOGLE_API_KEY') else '❌ 미설정'}
  • TYPECAST_API_KEY: {'✅ 설정됨' if os.getenv('TYPECAST_API_KEY') else '❌ 미설정'}
  • ELEVENLABS_API_KEY: {'✅ 설정됨' if os.getenv('ELEVENLABS_API_KEY') else '❌ 미설정'}

[bold]에셋 상태:[/bold]
  • B-roll 영상: {broll_count}개
  • BGM: {bgm_count}개

[bold]사용 가능한 채널:[/bold]
  • stoic: 스토아 철학/동기부여
  • english: 영어학습 (준비 중)

[dim]자세한 사용법: python main.py --help[/dim]
""",
        title="ℹ️ 시스템 정보",
        expand=False
    ))


# ============================================================
# 파이프라인 명령어
# ============================================================

@cli.command()
@click.argument('quote_id', type=int)
@click.option('--hook', '-h', default='H1', help='훅 유형 (H1-H5)')
@click.option('--cta', '-t', default='C3', help='CTA 유형 (C1-C5)')
@click.option('--channel', '-c', default='stoic', help='채널 유형')
@click.option('--with-tts', is_flag=True, help='TTS 음성 생성 사용 (기본: 직접 녹음)')
@click.option('--skip-video', is_flag=True, help='영상 합성 건너뛰기')
def run(quote_id, hook, cta, channel, with_tts, skip_video):
    """
    전체 파이프라인 실행

    명언 ID로 스크립트 생성부터 영상 합성까지 전체 파이프라인을 실행합니다.

    \b
    예시:
      python main.py run 1                    # 명언 #1로 전체 파이프라인 실행
      python main.py run 1 --skip-video       # 영상 합성 제외
      python main.py run 1 -h H2 -t C1        # 훅/CTA 유형 지정
    """
    try:
        from pipeline import Pipeline, PipelineConfig

        console.print(Panel(
            f"""[bold cyan]🎬 파이프라인 실행[/bold cyan]

명언 ID: {quote_id}
훅 유형: {hook}
CTA 유형: {cta}
채널: {channel}
TTS 사용: {'예' if with_tts else '아니오 (직접 녹음)'}
영상 건너뛰기: {'예' if skip_video else '아니오'}
""",
            title="설정",
            expand=False
        ))

        # 파이프라인 설정
        config = PipelineConfig()
        config.channel = channel
        config.default_hook_type = hook
        config.default_cta_type = cta
        config.load_env()

        # 파이프라인 실행
        pipeline = Pipeline(config=config)
        result = pipeline.run(
            quote_id=quote_id,
            hook_type=hook,
            cta_type=cta,
            skip_tts=not with_tts,
            skip_video=skip_video
        )

        if result.success:
            console.print("\n[bold green]✅ 파이프라인 완료![/bold green]")
            console.print(f"  출력 폴더: [cyan]{result.output_dir}[/cyan]")
            console.print(f"  소요 시간: {result.duration_seconds:.1f}초")

            if result.video_path and result.video_path.exists():
                console.print(f"  영상: [green]{result.video_path}[/green]")
            if result.audio_path and result.audio_path.exists():
                console.print(f"  오디오: [green]{result.audio_path}[/green]")
            if result.metadata_path and result.metadata_path.exists():
                console.print(f"  메타데이터: [green]{result.metadata_path}[/green]")
        else:
            console.print(f"\n[bold red]❌ 파이프라인 실패[/bold red]")
            console.print(f"  오류: {result.error}")
            sys.exit(1)

    except ImportError as e:
        console.print(f"[red]오류: 필요한 모듈을 불러올 수 없습니다.[/red]")
        console.print(f"[dim]{e}[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('quote_ids', type=str)
@click.option('--hook', '-h', default='H1', help='훅 유형 (H1-H5)')
@click.option('--cta', '-t', default='C3', help='CTA 유형 (C1-C5)')
@click.option('--channel', '-c', default='stoic', help='채널 유형')
@click.option('--with-tts', is_flag=True, help='TTS 음성 생성 사용 (기본: 직접 녹음)')
@click.option('--skip-video', is_flag=True, help='영상 합성 건너뛰기')
def batch(quote_ids, hook, cta, channel, with_tts, skip_video):
    """
    배치 파이프라인 실행

    여러 명언을 한 번에 처리합니다.

    \b
    QUOTE_IDS 형식:
      - 쉼표 구분: "1,2,3"
      - 범위: "1-5"
      - 혼합: "1,3,5-10"

    \b
    예시:
      python main.py batch "1,2,3"            # 명언 1, 2, 3 처리
      python main.py batch "1-5"              # 명언 1~5 처리
      python main.py batch "1,3,5-7"          # 혼합 형식
    """
    # ID 파싱
    ids = _parse_quote_ids(quote_ids)

    if not ids:
        console.print("[red]오류: 유효한 명언 ID가 없습니다.[/red]")
        sys.exit(1)

    console.print(Panel(
        f"""[bold cyan]🎬 배치 파이프라인 실행[/bold cyan]

대상 명언: {len(ids)}개 ({', '.join(map(str, ids[:5]))}{'...' if len(ids) > 5 else ''})
훅 유형: {hook}
CTA 유형: {cta}
채널: {channel}
""",
        title="배치 설정",
        expand=False
    ))

    try:
        from pipeline import Pipeline, PipelineConfig

        config = PipelineConfig()
        config.channel = channel
        config.load_env()

        pipeline = Pipeline(config=config)
        results = pipeline.run_batch(
            quote_ids=ids,
            hook_type=hook,
            cta_type=cta,
            skip_tts=not with_tts,
            skip_video=skip_video
        )

        # 결과 요약
        success_count = sum(1 for r in results if r.success)
        total = len(results)

        console.print("\n" + "=" * 50)
        console.print(f"[bold]배치 완료: {success_count}/{total} 성공[/bold]")
        console.print("=" * 50)

        if success_count < total:
            console.print("\n[yellow]실패한 항목:[/yellow]")
            for i, r in enumerate(results):
                if not r.success:
                    console.print(f"  • 명언 #{ids[i]}: {r.error}")

    except Exception as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


def _parse_quote_ids(ids_str: str) -> List[int]:
    """명언 ID 문자열 파싱"""
    ids = []
    parts = ids_str.split(',')

    for part in parts:
        part = part.strip()
        if '-' in part:
            # 범위 (예: "1-5")
            try:
                start, end = part.split('-')
                ids.extend(range(int(start), int(end) + 1))
            except ValueError:
                continue
        else:
            # 단일 ID
            try:
                ids.append(int(part))
            except ValueError:
                continue

    return sorted(set(ids))


@cli.command()
@click.option('--channel', '-c', default='stoic', help='채널 유형')
def scan_broll(channel):
    """B-roll 폴더 스캔 및 인덱스 갱신"""
    try:
        from core.broll_selector import BrollSelector

        broll_path = ASSETS_DIR / 'b-roll'

        if not broll_path.exists():
            console.print(f"[yellow]B-roll 폴더가 없습니다. 생성합니다...[/yellow]")
            broll_path.mkdir(parents=True, exist_ok=True)
            (broll_path / 'nature').mkdir(exist_ok=True)
            (broll_path / 'city').mkdir(exist_ok=True)
            (broll_path / 'abstract').mkdir(exist_ok=True)
            console.print(f"[green]폴더 생성 완료: {broll_path}[/green]")
            return

        selector = BrollSelector(assets_path=broll_path)
        selector.refresh_index()

        stats = selector.get_stats()

        console.print(Panel(
            f"""[bold cyan]B-roll 인덱스 갱신 완료[/bold cyan]

총 클립 수: {stats['total_clips']}개
총 길이: {stats['total_duration']:.1f}초
평균 길이: {stats['avg_duration']:.1f}초

[bold]테마별 분포:[/bold]
{chr(10).join(f"  • {theme}: {count}개" for theme, count in stats['themes'].items())}
""",
            title="📹 B-roll 스캔 결과",
            expand=False
        ))

    except Exception as e:
        console.print(f"[red]오류: {e}[/red]")
        sys.exit(1)


@cli.command()
def setup():
    """초기 설정 및 폴더 구조 생성"""
    console.print("[bold cyan]🔧 Shorts Factory 초기 설정[/bold cyan]\n")

    # 폴더 생성
    folders = [
        OUTPUT_DIR,
        ASSETS_DIR / 'b-roll' / 'nature',
        ASSETS_DIR / 'b-roll' / 'city',
        ASSETS_DIR / 'b-roll' / 'abstract',
        ASSETS_DIR / 'bgm',
        ASSETS_DIR / 'fonts',
    ]

    for folder in folders:
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            console.print(f"  [green]✓[/green] 생성됨: {folder}")
        else:
            console.print(f"  [dim]○[/dim] 존재함: {folder}")

    # .env 파일 확인
    env_file = CONFIG_DIR / '.env'
    env_example = CONFIG_DIR / '.env.example'

    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        console.print(f"\n  [green]✓[/green] .env 파일 생성됨 (config/.env)")
        console.print("  [yellow]→ API 키를 설정하세요![/yellow]")
    elif not env_file.exists():
        console.print(f"\n  [yellow]⚠[/yellow] .env 파일을 수동으로 생성하세요")
    else:
        console.print(f"\n  [dim]○[/dim] .env 파일 존재함")

    console.print("\n[bold green]✅ 초기 설정 완료![/bold green]")
    console.print("\n다음 단계:")
    console.print("  1. config/.env 파일에 API 키 설정")
    console.print("  2. assets/b-roll/ 에 배경 영상 추가")
    console.print("  3. assets/bgm/ 에 배경 음악 추가")
    console.print("  4. python main.py run 1 로 테스트")


if __name__ == '__main__':
    cli()
