import gspread
gc=gspread.service_account(filename='credentials.json')
sh=gc.open_by_key("1bbUa0EFTwPghoFDUKsJi-Xh8nXxao9v-6MBg8msjGHg")
worksheet =sh.worksheet("uid")
# worksheet_list = sh.worksheets()
# worksheet=sh.sheet2
list_of_lists = worksheet.get_all_values()
print(list_of_lists)