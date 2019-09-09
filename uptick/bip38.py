# -*- coding: utf-8 -*-
import click
from tqdm import tqdm
from .decorators import online
from .main import main
from .ui import print_table


@main.group()
def bip38():
    """ Further bip38
    """
    pass


@bip38.command()
@click.pass_context
@online
@click.argument("encrypted_wif", nargs=-1)
def decrypt(ctx, encrypted_wif):
    """ Return decrypted wif
    """
    from bitsharesbase.bip38 import decrypt
    from bitsharesbase.account import PrivateKey, Address
    from graphenebase.account import GrapheneAddress

    password = click.prompt("Passphrase", hide_input=True).strip()
    t = [["wif", "pubkey", "accounts", "addresses"]]
    for encwif in tqdm(encrypted_wif):
        while True:
            try:
                wif = PrivateKey(decrypt(encwif, password))
                break
            except Exception as e:
                print(str(e))
                password = click.prompt("Passphrase", hide_input=True).strip()

        pubkey = str(wif.pubkey)
        t.append(
            [
                str(wif),
                pubkey,
                ctx.bitshares.wallet.getAccountFromPublicKey(pubkey) or "",
                "\n".join(
                    [
                        str(
                            Address.from_pubkey(wif.pubkey, compressed=True, version=0)
                        ),
                        str(
                            Address.from_pubkey(wif.pubkey, compressed=False, version=0)
                        ),
                        str(
                            Address.from_pubkey(wif.pubkey, compressed=True, version=56)
                        ),
                        str(
                            Address.from_pubkey(
                                wif.pubkey, compressed=False, version=56
                            )
                        ),
                        str(GrapheneAddress.from_pubkey(wif.pubkey, compressed=False)),
                        str(GrapheneAddress.from_pubkey(wif.pubkey, compressed=True)),
                    ]
                ),
            ]
        )
    print_table(t)
