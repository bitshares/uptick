import click
from bitshares.account import Account
from bitshares.amount import Amount
from bitshares.vesting import Vesting
from .decorators import online
from .main import main, config
from .ui import print_table


class Vote:
    WITNESS = "witness"
    COMMITTEE = "committee"
    WORKER = "worker"

    @staticmethod
    def types():
        return [Vote.WITNESS, Vote.COMMITTEE, Vote.WORKER]

    @staticmethod
    def vote_type_from_id(id):
        if id[:4] == "1.6.":
            return Vote.WITNESS
        elif id[:4] == "1.5.":
            return Vote.COMMITTEE
        elif id[:5] == "1.14.":
            return Vote.WORKER


@main.command()
@click.argument("account", default=config["default_account"])
@click.option("--type", default=Vote.types())
@click.pass_context
@online
def votes(ctx, account, type):
    """ List accounts vesting balances
    """
    if not isinstance(type, (list, tuple)):
        type = [type]
    account = Account(account, full=True)
    ret = {key: list() for key in Vote.types()}
    for vote in account["votes"]:
        t = Vote.vote_type_from_id(vote["id"])
        ret[t].append(vote)

    t = [["id", "url", "account"]]
    for vote in ret["committee"]:
        t.append(
            [vote["id"], vote["url"], Account(vote["committee_member_account"])["name"]]
        )

    if "committee" in type:
        t = [["id", "url", "account", "votes"]]
        for vote in ret["committee"]:
            t.append(
                [
                    vote["id"],
                    vote["url"],
                    Account(vote["committee_member_account"])["name"],
                    str(Amount({"amount": vote["total_votes"], "asset_id": "1.3.0"})),
                ]
            )
        print_table(t)

    if "witness" in type:
        t = [
            [
                "id",
                "account",
                "url",
                "votes",
                "last_confirmed_block_num",
                "total_missed",
                "westing",
            ]
        ]
        for vote in ret["witness"]:
            t.append(
                [
                    vote["id"],
                    Account(vote["witness_account"])["name"],
                    vote["url"],
                    str(Amount({"amount": vote["total_votes"], "asset_id": "1.3.0"})),
                    vote["last_confirmed_block_num"],
                    vote["total_missed"],
                    str(Vesting(vote.get("pay_vb")).claimable)
                    if vote.get("pay_vb")
                    else "",
                ]
            )
        print_table(t)

    if "worker" in type:
        t = [["id", "name/url", "daily_pay", "votes", "time", "account"]]
        for vote in ret["worker"]:
            votes = Amount({"amount": vote["total_votes_for"], "asset_id": "1.3.0"})
            amount = Amount({"amount": vote["daily_pay"], "asset_id": "1.3.0"})
            t.append(
                [
                    vote["id"],
                    "{name}\n{url}".format(**vote),
                    str(amount),
                    str(votes),
                    "{work_begin_date}\n-\n{work_end_date}".format(**vote),
                    str(Account(vote["worker_account"])["name"]),
                ]
            )
        print_table(t)
