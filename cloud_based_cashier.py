import gspread
from tkinter import *
from tkinter import ttk
root = Tk()

gc=gspread.service_account(filename='credentials.json')
sh=gc.open_by_key("1bbUa0EFTwPghoFDUKsJi-Xh8nXxao9v-6MBg8msjGHg")
worksheet=sh.sheet1
list_of_lists = worksheet.get_all_values()

print(list_of_lists)



col_dict={
    "ProductName":1,
    "NumberAvailable":2,
    "NumberSold":3,
    "SellingPrice":4,
    "Cost":5,
    "Profit":6,
    "TotalProfit":7,
    "TotalNumberEverAdded":8,
    "ToalNumberEverSold":9}




product_names = worksheet.col_values(col_dict[col_name])

pnames=StringVar(value=product_names)
number_available=StringVar()



content=ttk.Frame(root,padding=(5,5,12,0))
content.grid(column=0,row=0,sticky=(N,W,E,S))
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0,weight=1)


def ifAvailable(*args):
    idxs=productbox.curselection()
    if len(idxs)==1:
        idx=int(idxs[0])
        productNumberAvailable=product_names[idx]
        if productNumberAvailable=="":
            number_available.set(" In stock: %d" % (name, code, popn))
        if productNumberAvailable>1 :
            number_available.set(" In stock: %d" % (name, code, popn))
        else:
            number_available.set("Not Available")
productbox=Listbox(content,listvariable=pnames,height=5)
isavailablelbl = ttk.Label(content, textvariable=number_available, anchor='center')

productbox.grid(column=0, row=0, rowspan=6, sticky=(N,S,E,W))
isavailablelbl.grid(column=2, row=4, sticky=E)
productbox.bind('<<ListboxSelect>>',ifAvailable)
number_available.set('')
productbox.selection_set(0)
ifAvailable()

root.mainloop()














































 # copy the key from the link

# res=worksheet.get_all_records() #give me a dictionary
# res=worksheet.get_all_values() #a list of all rows
# res=worksheet.row_values(1)# to get the row specified indices start as q not zero
# res=worksheet.col_values(1)
# res=worksheet.get("A2") # to get a particular cell
# res=worksheet.get("A2:C2") #for a range
# #create  new user 
# user=["susan","immwpwmde","njenni"]
# worksheet.insert_row (user,3)
# worksheet.append_row (user,3)
# worksheet.update(row_number,col_number,value)
# print(res)