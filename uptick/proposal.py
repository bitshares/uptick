import json
import click
from bitshares.proposal import Proposals
from bitshares.account import Account
from .decorators import onlineChain, unlockWallet
from .main import main, config
from .ui import print_table, print_tx, format_dict


@main.command()
@click.pass_context
@onlineChain
@click.argument("proposal", nargs=-1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str,
)
@unlockWallet
def disapproveproposal(ctx, proposal, account):
    """ Disapprove a proposal
    """
    print_tx(ctx.bitshares.disapproveproposal(proposal, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("proposal", nargs=-1)
@click.option(
    "--account",
    help="Account that takes this action",
    default=config["default_account"],
    type=str,
)
@unlockWallet
def approveproposal(ctx, proposal, account):
    """ Approve a proposal
    """
    print_tx(ctx.bitshares.approveproposal(proposal, account=account))


@main.command()
@click.pass_context
@onlineChain
@click.argument("account", default=config["default_account"], type=str, required=False)
def proposals(ctx, account):
    """ List proposals
    """
    proposals = Proposals(account)
    t = [
        [
            "id",
            "expiration",
            "proposer",
            "required approvals",
            "available approvals",
            "review period time",
            "proposal",
        ]
    ]
    for proposal in proposals:
        t.append(
            [
                proposal["id"],
                proposal["expiration_time"],
                Account(proposal.proposer)["name"],
                [
                    Account(x)["name"]
                    for x in (
                        proposal["required_active_approvals"]
                        + proposal["required_owner_approvals"]
                    )
                ],
                json.dumps(
                    [Account(x)["name"] for x in proposal["available_active_approvals"]]
                    + proposal["available_key_approvals"]
                    + proposal["available_owner_approvals"],
                    indent=1,
                ),
                proposal.get("review_period_time", None),
                format_dict(proposal["proposed_transaction"]),
            ]
        )

    print_table(t)
