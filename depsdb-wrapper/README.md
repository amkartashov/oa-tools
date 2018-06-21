# Depsdb.pl wrapper #

## Purpose ##

Automate cleanup of test accounts with depsdb.pl

## Usage ##

* Backup Operations and Billing databases
* Copy attached scripts to the same folder on Billing application server, e.g. /root/cleanup
* Prepare file with account IDs, one per line, say /root/cleanup/accounts.to.delete
* Run script:
    ```
    [root@bss cleanup]# python -u cleanup.py accounts.to.delete 2>&1 | tee -a cleanup.output
    ======= Deleting account 1000005
      Remove SQL:
        DELETE FROM "Users" WHERE "UsersID"='1000007';
        DELETE FROM "AccountInheritance" WHERE "CustomerAccountID"='1000005' AND "VendorAccountID"='1';
        DELETE FROM "IntUsers" WHERE "UsersID"='1000007';
        DELETE FROM "Role" WHERE "RoleID"='107';
        DELETE FROM "IntAccount" WHERE "AccountID"='1000005';
    ..Removing account from OA
    ..Executing remove SQL
    ```

## Troubleshooting ##

Script may fail somewhere in between, e.g. with API exception while removing account in Operations. In this case, it may happen that SQL queries were partly executed. You need to:

    * Remove already deleted accounts IDs from accounts.to.delete
    * Fix the reason of API exception
    * If account gets deleted, execute queries from "Remove SQL" section manually in Billing database and remove this account ID form accounts.to.delete
    * Re-run script

## Known issues ##

### depsdb.pl does not work on RedHat 7

Error message: "Failed to determine OS"

W/A: update constant REDHAT_DISTR in /usr/local/bm/tools/helper.pm adding this line:

    "Red Hat Enterprise Linux Server release 7" => "el6",







