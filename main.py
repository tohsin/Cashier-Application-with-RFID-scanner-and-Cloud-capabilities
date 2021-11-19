import gspread
from tkinter import *
from tkinter import ttk
from tkinter import messagebox as msg
import threading
import urllib.request
import serial
import time
import serial.tools.list_ports
from PIL import Image, ImageTk

class App():
    def __init__(self, root):
        # program variables
        self.list_of_lists = []
        self.product_names = []
        self.cardsIdToAssign = {}
        self.cart_ids = {}
        self.scan = False
        self.data_index = {
            'ProductName': 0,
            'NumberAvailable': 1,
            'NumberSold': 2,
            'SellingPrice': 3,
            'Cost': 4,
            'Profit': 5,
            'TotalProfit': 6,
            'TotalNumberEverAdded': 7,
            'TotalNumberEverSold': 8
        }
        self.state = "nothing"
        self.currentCost = [0, 0]
        # self.arduino = serial.Serial(port='COM3', baudrate=9600, timeout=.1)
        # if not self.arduino.isOpen():
        #     self.arduino.open()

        # declare tkinter variables
        self.stockAdding_tvar = StringVar()
        self.pnames_tvar = StringVar(value=self.product_names)  # variables on tkinter
        self.numberAvailable_tvar = StringVar()
        self.totalCost_tvar = StringVar()
        self.cartState_tvar = StringVar()
        self.idScannedString = StringVar()
        self.asssignTag_tvar = StringVar()
        self.info = StringVar()

        self.header = Frame(root, width=800, height=300, bg='#C585B3')
        self.header.grid(columnspan=3, rowspan=6, row=0)

        self.base = Frame(root, width=800, height=100, bg='#D0A3BF')
        self.base.grid(columnspan=3, rowspan=1, row=6)

        # Add to stock btn
        self.addToStock_btn = Button(root, textvariable=self.stockAdding_tvar, font=('shanti', 10),
                                     command=self.add_to_stock_btn_fn, height=1, width=15)
        self.addToStock_btn.grid(row=1, column=2, sticky=(N))

        # Add to cart button
        self.addToCart_btn = Button(root, textvariable=self.cartState_tvar,
                                    command=self.createcart_btn_fn, font=('shanti', 10), height=1, width=15, )
        self.addToCart_btn.grid(row=1, column=1, sticky=(N))

        # Checkout Button
        self.proceedToCheckpoint_btn = Button(root, text='Checkout', font=('shanti', 10),
                                              height=1, width=15, command=self.checkout_btn_fn, default='active',
                                              )
        self.proceedToCheckpoint_btn.grid(column=2, row=3)

        # Assign tag Button
        self.assignTag_btn = Button(root, textvariable=self.asssignTag_tvar, font=('shanti', 10),
                                    height=1, width=15, command=self.assign_tag_btn_fn, default='active',
                                    )
        self.assignTag_btn.grid(column=2, row=2)

        self.refreshupdate_btn = Button(root, text='refresh', font=('shanti,10')
                                        , width=7, command=self.refresh_btn_fn)

        # first listbox widget
        self.pbox = Listbox(root, listvariable=self.pnames_tvar, bg="#D6BBC0",
                            activestyle='dotbox', fg='black', )
        self.pbox.grid(row=1, column=0, rowspan=4, sticky=(N, W, E, S), padx=(50, 50), pady=(5, 5))

        # secound box widget
        self.cbox = Listbox(root, bg="#D6BBC0",
                            activestyle='dotbox', fg='black', )
        self.cbox.grid(row=2, column=1, rowspan=3, padx=(30, 30), pady=(5, 5), sticky=(N, W, E, S))

        # in stock widget text
        self.in_stock_txt = Label(root, textvariable=self.numberAvailable_tvar,bg='#C585B3')
        self.in_stock_txt.grid(row=5, column=0, sticky=N)

        # cost widget
        self.totalCost_txt = Label(root, textvariable=self.totalCost_tvar,bg='#C585B3')
        self.totalCost_txt.grid(row=5, column=1, sticky=N)

        # information widget
        self.info_txt = Label(root, textvariable=self.info, bg='#D0A3BF', fg='black')
        self.info_txt.grid(row=6, column=1, rowspan=3)

        # binding list view
        self.pbox.bind('<<ListboxSelect>>', self.ifAvailable)
        self.cbox.bind('<Double-1>', self.removeFromCart)

        # set state of buttons
        self.proceedToCheckpoint_btn.configure(state='disabled')
        self.addToStock_btn.configure(state='disabled')
        self.addToCart_btn.configure(state='disabled')
        self.assignTag_btn.configure(state='disabled')

        # tkinter variables assigned values
        self.numberAvailable_tvar.set('')
        self.cartState_tvar.set('Create Cart')
        self.stockAdding_tvar.set('Add to Stock')
        self.asssignTag_tvar.set('Assign Tag')
        self.totalCost_tvar.set('%d items, Total Cost : %d Naira' % (0, 0))
        self.info.set('Starting........ Hold on')
        self.pbox.selection_set(0)
        self.arduino = self.load_arduino()
        if (self.arduino != "error"):
            if not self.arduino.isOpen():
                self.arduino.open()
            threading.Thread(target=self.update).start()

        else:
            self.info.set('Please Connect Scanner To use The Software')
        # function to load intitial data

    def refresh_btn_fn(self, *args):
        threading.Thread(target=self.update).start()
        self.refreshupdate_btn.grid_forget()

    def assign_tag_btn_fn(self, *args):
        if (self.state == 'nothing'):
            self.asssignTag_tvar.set('Save')
            self.state = 'registeringCard'
            self.scan = True
            self.addToCart_btn.configure(state='disabled')
            self.addToStock_btn.configure(state='disabled')
            threading.Thread(target=self.scanID, args=(1,)).start()
            self.info.set("Select product name to write card to ")
        elif (self.state == 'registeringCard'):
            self.scan = False
            self.arduino.close()
            self.asssignTag_tvar.set('Assign Tag')
            self.state = 'nothing'
            self.info.set("Currently Assigning cards to Product Please Hold on !!!")
            threading.Thread(target=self.handle_assign_cloud).start()
            self.addToCart_btn.configure(state='active')
            self.addToStock_btn.configure(state='active')

    def checkout_btn_fn(self, *args):
        if self.currentCost[0] == 0:
            msgbox = msg.showinfo("Note", 'No Item in Cart... \n Please add to cart to continue')
        else:
            msgbox = msg.askokcancel("Notice",
                                     "Do you wish to check out your product \n    You have %s items that cost %d Naira" % (
                                         self.currentCost[1], self.currentCost[0]))
            if msgbox:
                self.cbox.delete(0, END)
                self.state = 'nothing'
                self.scan = False
                self.arduino.close()
                print("makesale")
                threading.Thread(target=self.makeSale, args=(self.cart_ids,)).start()
                self.cartState_tvar.set('Create Cart')
                self.proceedToCheckpoint_btn.configure(state='disabled')
                self.currentCost[0] = 0
                self.currentCost[1] = 0
                self.totalCost_tvar.set('%d items, Total Cost : %d Naira' % (0, 0))

    def add_to_stock_btn_fn(self, *args):
        print(self.state)
        if (self.state == 'nothing'):
            self.stockAdding_tvar.set('Save')
            self.state = 'addingtostock'
            self.scan = True
            self.addToCart_btn.configure(state='disabled')
            self.assignTag_btn.configure(state='disabled')
            threading.Thread(target=self.scanID, args=(0,)).start()
        elif (self.state == 'addingtostock'):
            self.scan = False
            self.arduino.close()
            if (len(self.cart_ids) > 0):
                threading.Thread(target=self.saveToCloudStock, args=(self.cart_ids,)).start()
            else:
                self.info.set('Stock was empty ')
                self.addToCart_btn.configure(state='active')
            self.stockAdding_tvar.set('Add to Stock')
            self.state = 'nothing'

    def createcart_btn_fn(self, *args):  # funtions for button to create cart
        if (self.state == 'nothing'):
            self.info.set('Place RFID tag to add to cart')
            self.cartState_tvar.set('Cancel')
            self.state = 'creatingcart'
            self.scan = True
            self.addToStock_btn.configure(state='disabled')
            self.assignTag_btn.configure(state='disabled')
            self.proceedToCheckpoint_btn.configure(state='active')
            threading.Thread(target=self.scanID, args=(0,)).start()
        elif (self.state == 'creatingcart'):
            self.cartState_tvar.set('Create Cart')
            self.addToStock_btn.configure(state='active')
            self.assignTag_btn.configure(state='active')
            self.proceedToCheckpoint_btn.configure(state='disabled')
            self.state = 'nothing'
            self.scan = False
            self.arduino.close()
           # threading.Thread(target=self.scanID, args=(0,)).start()
            self.cbox.delete(0, END)
            self.cart_ids.clear()
            self.currentCost[0] = 0
            self.currentCost[1] = 0
            self.totalCost_tvar.set('%d items, Total Cost : %d Naira' % (0, 0))

    def load_arduino(self):
        for pinfo in serial.tools.list_ports.comports():
            if pinfo.serial_number == "55736303631351B0F1A1":
                return serial.Serial(pinfo.device)
        return "error"

    def update(self):
        if (self.is_connected()):
            if (self.refreshupdate_btn.winfo_ismapped()):
                self.refreshupdate_btn.grid_forget()
            self.info.set('Loading.... Please Hold on')
            try:
                gc = gspread.service_account(filename='credentials.json')
                sh = gc.open_by_key("1bbUa0EFTwPghoFDUKsJi-Xh8nXxao9v-6MBg8msjGHg")
                self.worksheet = sh.sheet1
                self.worksheet2 = sh.worksheet("uid")
                self.uid_maps = self.worksheet2.get_all_values()
                print(self.uid_maps)
                self.list_of_lists = self.worksheet.get_all_values()
                self.info.set('')
                self.cbox.delete(0, END)
                self.selling_prices = self.extract_col(self.list_of_lists, self.data_index['SellingPrice'])
                self.product_names = self.extract_col(self.list_of_lists, self.data_index["ProductName"])
                print(self.product_names)
                for i in range(len(self.product_names)):
                    self.pbox.insert(i, self.product_names[i])
                self.pbox.selection_set(0)
                self.addToCart_btn.configure(state='active')
                self.addToStock_btn.configure(state='active')
                self.assignTag_btn.configure(state='active')
                self.ifAvailable()
            except Exception as e:
                self.info.set('Problem When  Connecting To Cloud ')
                self.refreshupdate_btn.grid(row=6, column=2)
        else:
            self.info.set('Problem When  Connecting To Internet')
            self.refreshupdate_btn.grid(row=6, column=2)

        print("Ended update")

    def is_connected(self):
        try:
            urllib.request.urlopen('http://google.com')  # Python 3.x
            return True
        except:
            return False

    def extract_col(self, data_sheet, index):
        data = []
        for row in range(1, len(data_sheet)):
            data.append(data_sheet[row][index])
        return data

    # print(extrct_col(list_of_lists,data_index["ProductName"]))


    def ifAvailable(self, *args):
        if len(self.product_names) != 0:
            idxs = self.pbox.curselection()
            if len(idxs) == 1:
                idx = int(idxs[0])
                list_of_available = self.extract_col(self.list_of_lists, self.data_index["NumberAvailable"])
                productNumberAvailable = list_of_available[idx]
                if productNumberAvailable == " ":
                    self.numberAvailable_tvar.set("Not Available")
                if productNumberAvailable == 0:
                    self.numberAvailable_tvar.set("Not Available")
                else:
                    self.numberAvailable_tvar.set(
                        " In stock: %d ~ %d Naira" % (int(productNumberAvailable), int(self.selling_prices[idx])))


    def makeSale(self, cart):
        self.info.set("Please hold on while we update and confirm your sale")
        self.proceedToCheckpoint_btn.configure(state='disabled')
        self.addToStock_btn.configure(state='disabled')
        self.addToCart_btn.configure(state='disabled')
        print(cart)
        for key in cart:
            try:
                values_list = self.worksheet.row_values(key + 2)
                self.worksheet.update_cell(key + 2, 2, int(values_list[1]) - cart[key][0])  #
                self.worksheet.update_cell(key + 2, 3, int(values_list[2]) + cart[key][0])
                self.worksheet.update_cell(key + 2, 7, int(values_list[6]) + int(values_list[5]))
                self.worksheet.update_cell(key + 2, 9, int(values_list[8]) + cart[key][0])
                print(self.worksheet.row_values(key + 2))

            except Exception as e:
                print(e)
        self.cart_ids.clear()
        threading.Thread(target=self.update).start()
        self.pbox.delete(0, END)
        self.numberAvailable_tvar.set('')
        self.info.set("Sale succesfully backed up")
        self.addToStock_btn.configure(state='active')
        self.addToCart_btn.configure(state='active')

    def saveToCloudStock(self, cart):  # funtion loops to take stock
        self.info.set("Please hold on while we update and add to stock")
        self.proceedToCheckpoint_btn.configure(state='disabled')
        self.addToStock_btn.configure(state='disabled')
        self.addToCart_btn.configure(state='disabled')
        for key in cart:
            try:
                values_list = self.worksheet.row_values(key + 2)
                self.worksheet.update_cell(key + 2, 2, int(values_list[1]) + cart[key][0])  # add to number available
                self.worksheet.update_cell(key + 2, 8,
                                           int(values_list[7]) + cart[key][0])  # add to total number ever added
                print(self.worksheet.row_values(key + 2))
            except Exception as e:
                print(e)
        self.cart_ids.clear()
        self.pbox.delete(0, END)
        self.currentCost[0] = 0
        self.currentCost[1] = 0
        self.totalCost_tvar.set('%d items, Total Cost : %d Naira' % (0, 0))
        self.numberAvailable_tvar.set('')
        threading.Thread(target=self.update).start()
        self.info.set("Sale succesfully backed up")
        self.addToStock_btn.configure(state='active')
        self.addToCart_btn.configure(state='active')


    def removeFromCart(self, *args):
        idxs = self.cbox.curselection()
        if len(idxs) == 1:
            idx = int(idxs[0])
            keys_ = list(self.cart_ids.keys())
            keywearelookingfor = keys_[idx]

            self.currentCost[1] -= 1
            self.currentCost[0] -= int(self.selling_prices[int(keywearelookingfor)])
            print(self.cart_ids)
            if self.cart_ids[keywearelookingfor][0] == 1:
                del self.cart_ids[keywearelookingfor]
                self.cbox.delete(idx)
            else:
                self.cart_ids[keywearelookingfor][0] -= 1
                self.cbox.delete(idx)
                string_cart_item = "%s : %d " % (
                self.product_names[int(keywearelookingfor)], self.cart_ids[keywearelookingfor][0])
                self.cbox.insert(idx, string_cart_item)
        self.totalCost_tvar.set('%d items, Total Cost : %d Naira' % (self.currentCost[1], self.currentCost[0]))

    def scanID(self, mode):
        if (self.arduino != "error"):
            if not self.arduino.isOpen():
                self.arduino.open()
        else:
            self.info.set('Please Connect Scanner To use The Software')
        self.str_ = ""
        while True:
            if (not self.scan):
                self.str_ = ""
                break
            data = self.arduino.readline()
            if (not self.scan):
                self.str_ = ""
                break
            str_rn = data.decode()
            self.str_ = str_rn.rstrip()
            print(len(self.str_))
            if (self.str_ != ""):
                id = self.findId(self.str_, self.uid_maps)

                if (mode == 0):

                    print('trying add to cart or add to stock')
                    if (id != 'not found'):
                        self.currentCost[0] += int(self.selling_prices[int(id)])
                        self.currentCost[1] += 1
                        if id in self.cart_ids:
                            self.cart_ids[id][0] += 1
                            self.cbox.delete(self.cart_ids[id][1])
                            string_cart_item = "%s : %d " % (self.product_names[int(id)], self.cart_ids[id][0])
                            self.cbox.insert(self.cart_ids[id][1], string_cart_item)
                        else:
                            self.cart_ids[id] = [1, self.cbox.size()]
                            string_cart_item = "%s : %d " % (self.product_names[int(id)], self.cart_ids[id][0])
                            self.cbox.insert(self.cart_ids[id][1], string_cart_item)
                        self.totalCost_tvar.set('Total Cost : %d Naira' % (self.currentCost[0]))
                        self.totalCost_tvar.set(
                            '%d items, Total Cost : %d Naira' % (self.currentCost[1], self.currentCost[0]))
                        self.idScannedString.set('')
                        self.str_ = ""
                    else:
                        self.info.set(
                            "Card not recognised please swipe well or Assign card")  # mode for creating card and
                elif (mode == 1):  # mode for registring new card

                    if (not self.scan):
                        self.str_ = ""
                        break
                    if(len(self.str_)!=12):
                        self.info.set("Hmm seems the card wasn't read properly,try again")
                    else:
                        idxs = self.pbox.curselection()
                        if len(idxs) == 1:
                            idx = int(idxs[0])
                        product_name = self.product_names[idx]
                        self.info.set("Assigning Card to {}".format(product_name))
                        self.cardsIdToAssign[self.str_] = product_name
                        self.str_ = ""
            time.sleep(2)
        try:
            self.arduino.close()
        except Exception as e:
            print(e)

        print("scanner closed")

    def handle_assign_cloud(self):
        postion = len(self.uid_maps) + 1
        for key in self.cardsIdToAssign:
            #card id wasnt found in data base
            id = self.find_id_assign(key, self.uid_maps)

            if(id=='not found'):
                try:
                    self.worksheet2.update_cell(postion, 2, key.strip())
                    self.worksheet2.update_cell(postion, 1,self.cardsIdToAssign[key])
                    postion+=1
                except Exception as e:
                    print(e)
                    self.info.set("Something Went wrong while uplading")
            else:
                try:
                    val = self.worksheet2.cell(id, 1).value
                    print(val)
                    self.worksheet2.update_cell(id, 1,self.cardsIdToAssign[key] )
                except Exception as e:
                    print(e)
                    self.info.set("Something Went wrong while uplading")
        self.cardsIdToAssign.clear()
        self.info.set("Cards Succefully assigned")
        threading.Thread(target=self.update).start()
    def findId(self, uid, uidlist):
        print(uid.strip())
        for i in range(1, len(uidlist)):
            print(uidlist[i][1].strip())
            if (uidlist[i][1].strip() == uid.strip()):
                self.index = self.product_names.index(uidlist[i][0])
                return self.index
        return 'not found'

    def find_id_assign(self,uid,uidlist):
        print(uid.strip())
        for i in range(1,len(uidlist)):
            if(uidlist[i][1].strip()== uid.strip()):
                return i+1
        return 'not found'
root = Tk()
app = App(root)

root.geometry('+%d+%d' % (350, 10))
ico = Image.open('cahsiericon.png')
photo = ImageTk.PhotoImage(ico)
root.wm_iconphoto(False, photo)
root.title('CaRFiD')
root.mainloop()


