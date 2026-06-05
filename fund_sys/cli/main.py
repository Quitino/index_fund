import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from data.models import init_db
from cli.commands.fetch import fetch
from cli.commands.simulate import simulate
from cli.commands.shadow_cmd import shadow
from cli.commands.valuation import valuation
from cli.commands.screen import screen
from cli.commands.batch_cmd import batch


@click.group()
def cli():
    """基金投资分析系统"""
    init_db()


cli.add_command(fetch)
cli.add_command(simulate)
cli.add_command(shadow)
cli.add_command(valuation)
cli.add_command(screen)
cli.add_command(batch)


if __name__ == "__main__":
    cli()
