#!/usr/bin/env python

import sys
import getpass
import fileinput
from subprocess import check_output

from poaupdater import uSysDB

from oaapi import OaApi, OaError

bm_root = '/usr/local/bm'
tools_dir = bm_root + '/tools'
depsdb_pl = bm_root + '/tools/depsdb.pl'

sys.path.append(bm_root + '/tools_py/')
import pba
from generic_classes import DBConfig

def init():
    pba.init(bm_root)
    bapi = pba.pbaapi.PBAAPIRaw()

    dbconfig = DBConfig(
        pba.conf.get('environment', 'DB_HOST'),
        pba.conf.get('environment', 'DB_NAME'),
        pba.conf.get('environment', 'DB_USER'),
        pba.conf.get('environment', 'DB_PASSWD'), 'PGSQL')
    uSysDB.init(dbconfig)
    con = uSysDB.connect()

    oaapihost, oaapiport = bapi.PEMGATE.PEMOptionsGet()['Result'][0]
    oaapihost = oaapihost.replace(" ", "")
    oapi = OaApi(oaapihost, oaapiport)

    return bapi, oapi, con

def remove_oa_account(account_id):
    subs = oapi.api_async_call_wait('pem.getAccountSubscriptions', account_id=account_id)
    for sub in subs:
        oapi.api_async_call_wait('pem.removeSubscription', timeout=300, subscription_id=sub)
    res = oapi.api_async_call_wait('pem.removeAccount', timeout=300, account_id=account_id)

def is_prepare_query(query):
    tables = ['ARDoc', 'AcceptedTerms', 'ADomain', 'UserToken', 'PayToolStatusHist']
    for t in tables:
        if query.startswith('DELETE FROM "{0}"'.format(t)):
            return True
    return False

def get_sql_queries(account_id):
    all_sql = check_output(cwd=tools_dir, args=[depsdb_pl, '-d', 'Account', 'AccountID={0}'.format(account_id), '--quiet']).split('\n')
    # remove comments and empty lines
    all_sql = [q for q in all_sql if not (q.startswith('--') or len(q) == 0)]
    prepare_sql = [q for q in all_sql if is_prepare_query(q)]
    remove_sql = [q for q in all_sql if not is_prepare_query(q)]
    return prepare_sql, remove_sql

def run_sql_queries(con, sql):
    cur = con.cursor()
    for q in sql:
        cur.execute(q)
    con.commit()

if __name__ == '__main__':
    bapi, oapi, con = init()
    for account_id in fileinput.input():
        account_id = int(account_id.strip())
        print("======= Deleting account {0}".format(account_id))
        if account_id:
            prepare_sql, remove_sql = get_sql_queries(account_id)
            if prepare_sql:
                print("  Prepare SQL:")
                for q in prepare_sql:
                    print("    {0}".format(q))
            print("  Remove SQL:")
            for q in remove_sql:
                print("    {0}".format(q))
            if prepare_sql:
                print("..Executing prepare SQL")
                run_sql_queries(con, prepare_sql)
            print("..Removing account from OA")
            remove_oa_account(account_id)
            print("..Executing remove SQL")
            run_sql_queries(con, remove_sql)



