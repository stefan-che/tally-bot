def get_filter_accounts(accounts: list, filters: list):
    filtered_accounts = []
    for account in accounts:
        for filter_string in filters:
            # * AND filter
            if "-" in filter_string:
                and_filters = filter_string.split("-")
                count = 0
                for and_filter in and_filters:
                    if and_filter in account.currency:
                        count += 1
                if count == len(and_filters):
                    filtered_accounts.append(account)

            elif filter_string in account.currency:
                filtered_accounts.append(account)
    return filtered_accounts