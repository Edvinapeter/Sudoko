# -*- coding: utf-8 -*-

import os
import time
from copy import deepcopy
from tkinter import *
from tkinter import Tk, Canvas, Frame, Button, BOTH, TOP, BOTTOM, filedialog,\
     Text, messagebox, Toplevel, Menubutton

MARGIN = 20     # Pixel um das Spiel 
SIDE = 60       # Breite jeder Zelle. 
WIDTH = HEIGHT = MARGIN * 2 + SIDE * 9      # Breite und Höhe des gesamten Spieles
ext = ".sudoku"
verzeichnis = "/home/pi/python-GUI/sudoku"

def openfile():
    dateiname = filedialog.askopenfilename(
                    initialdir= verzeichnis,
                    title="Dateiauswahl",
                    filetypes=(("sudoku Dateien", "*.sudoku"),("alle Dateien", "*.*")))
    return dateiname

def savefile():
    dateiname = filedialog.asksaveasfilename(
                    initialdir=verzeichnis,
                    title="Dateiauswahl",
                    filetypes=(("sudoku Dateien", "*.sudoku"),("alle Dateien", "*.*")))
    return dateiname

    
class SudokuError(Exception): 
    """ 
    Ein anwendungsspezifischer Fehler 
    """ 
    pass

class SudokuUI(Frame):
    """
    Die Tkinter Benutzeroberfläche
    Zeichnen des Boards, das Menü, die Eingaben und Ausgaben
    """
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.row, self.col = -1, -1
        self.__maxLoesung = 3
        self.__pruefung=BooleanVar()
        self.__pruefung.set(False)
        self.__geloest = False
        self.neueEingabe = False
        self.__auswahl=IntVar()
        self.__auswahl.set(1)
        self.__menu()
        self.game = ""
        self.__initUI()
        self.zaehle = 0

    def __initUI(self):
        self.parent.title("Sudoku  ")
        self.pack(fill=BOTH)
        self.canvas = Canvas(self, width=WIDTH, height=HEIGHT, bg="white")
        self.canvas.pack(fill=BOTH, side=TOP)
        self.__draw_grid()
        
        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __menu(self):
        menuBar = Menu(self.parent)
        fileMenu = Menu(menuBar, tearoff=0) # tearoff = Abreissparameter
        menuBar.add_cascade(label="Datei", menu=fileMenu)
        fileMenu.add_command(label="eingeben", command=self.__neue_datei)
        fileMenu.add_command(label="öffnen...", command=self.__andere_datei)
        fileMenu.add_command(label="speichern", command=self.__speichern_datei)
        fileMenu.add_separator()
        fileMenu.add_command(label="beenden", command=root.destroy)

        doMenu = Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="bearbeiten", menu=doMenu)
        doMenu.add_command(label="Eingaben löschen", command=self.__clear_answers)
        doMenu.add_command(label="Sudoku lösen", command=self.__loesung)

        einstellungMenu = Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="Einstellung", menu=einstellungMenu)
        einstellungMenu.add_radiobutton(variable=self.__pruefung, label="Prüfung ein",value=True)
        einstellungMenu.add_radiobutton(variable=self.__pruefung, label="Prüfung aus",value=False)
        einstellungMenu.add_command(label="Sudoku lösen", command=self.__loesung)

        hilfeMenu = Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="Hilfe", menu=hilfeMenu)
        hilfeMenu.add_radiobutton(variable=self.__auswahl, label="Datei", value=1, command=self.__hilfeAnzeige)
        hilfeMenu.add_radiobutton(variable=self.__auswahl, label="bearbeiten", value=2,command=self.__hilfeAnzeige)
        hilfeMenu.add_radiobutton(variable=self.__auswahl, label="Einstellung", value=3, command=self.__hilfeAnzeige)

        self.parent.config(menu=menuBar, width=WIDTH+10, height=HEIGHT+10)

    def __hilfeAnzeige(self):
        '''
        Hilfefenster darstellen mit dem entsprechenden Text
        '''
        hilfefenster = Toplevel(bd=5, relief=RAISED)
        hilfefenster.title("Hilfe ")
        hilfefenster.transient(self.parent)
        auswahl = self.__auswahl.get()
        if auswahl == 1:
            txt = '''                                Datei\n
eingeben
        Eingabe eines neuen Spieles\n
öffnen...
        öffnen einer vorhanden Datei mit Spieleingaben
        wenn welche gespeichert sind\n
speichern
        abspeichern des Spielstandes oder der Eingabe
        eines neuen Spieles\n
beenden
        beendet das Spiel\n'''
        elif auswahl == 2:
            txt = '''                             bearbeiten\n
Eingaben löschen
        Eingaben und Lösung werden entfernt\n
Sudoku lösen
        Das Sudoku wird gelöst und
        angezeigt\n'''
        else:
            txt = '''                            Einstellung\n
Prüfung ein
        Die Eingaben werden auf Übereinstimmung mit
        der Lösung geprüft\n
Prüfung aus
        Die Prüfung wird abgeschaltet, es wird nur
        auf bereits vorhandne geprüft\n 
Sudoku lösen
        Das Sudoku wird gelöst und angezeigt\n'''
        self.msg = Message(hilfefenster, text = txt)
        self.msg.config(font=('times', 12, 'normal'))
        self.msg.pack()
        self.button = Button(hilfefenster, text="Ok", width=15, bg="yellow", fg="blue", bd=5,
                             relief=RAISED, command=hilfefenster.destroy)
        self.button.pack()

    def __draw_grid(self):
        """
        Zeichnet ein mit blauen Linien geteiltes Gitter in 3x3 Quadrate
        """
        for i in range(10):
            farbe = "blue" if i % 3 == 0 else "black"
            dicke = 2 if i % 3 == 0 else 1

            x0 = MARGIN + i * SIDE
            y0 = MARGIN
            x1 = MARGIN + i * SIDE
            y1 = HEIGHT - MARGIN
            self.canvas.create_line(x0, y0, x1, y1, fill=farbe, width=dicke)

            x0 = MARGIN
            y0 = MARGIN + i * SIDE
            x1 = WIDTH - MARGIN
            y1 = MARGIN + i * SIDE
            self.canvas.create_line(x0, y0, x1, y1, fill=farbe, width=dicke)

    def __draw_puzzle(self, loesung = False):
        """
        Füllt das Gitter mit Ziffern in verschiedenen Farben (Fest, gespielt, Lösung)
        """
        self.canvas.delete("numbers")
        for i in range(9):
            for j in range(9):
                if self.__geloest and loesung:
                    answer = self.game.loes_puzzle[i][j]
                else:
                    answer = self.game.puzzle[i][j]
                if answer != 0:
                    x = MARGIN + j * SIDE + SIDE / 2
                    y = MARGIN + i * SIDE + SIDE / 2
                    original = self.game.start_puzzle[i][j]
                    if answer == original:
                        color = "black"
                    elif self.__geloest and loesung and answer != self.game.puzzle[i][j]:
                        answer = self.game.loes_puzzle[i][j]
                        color = "green"
                    else:
                        color = "magenta"
                    self.canvas.create_text(
                        x, y, text=answer, tags="numbers", fill=color, font=("Arial",14,"bold"))

    def __draw_cursor(self):
        """
        Zeichnet ein Quadrat um das ausgewählte Feld, wenn Eingabe möglich
        """
        self.canvas.delete("cursor")
        if self.row >= 0 and self.col >= 0:
            x0 = MARGIN + self.col * SIDE + 1
            y0 = MARGIN + self.row * SIDE + 1
            x1 = MARGIN + (self.col + 1) * SIDE - 1
            y1 = MARGIN + (self.row + 1) * SIDE - 1
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline="red", tags="cursor", width=3)

    def __draw_victory(self):
        """
        Zeichnet ein Oval (Kreis) und darin ein Text
        """
        x0 = y0 = MARGIN + SIDE * 2
        x1 = y1 = MARGIN + SIDE * 7
        self.canvas.create_oval(
            x0, y0, x1, y1,
            tags="victory", fill="dark orange", outline="orange")
        # erzeugt einen Text ins Oval
        x = y = MARGIN + 4 * SIDE + SIDE / 2
        self.canvas.create_text(
            x, y,
            text="Du hast es!", tags="victory",
            fill="white", font=("Arial", 32))

    def __cell_clicked(self, event):
        """
        reagiert auf Mouseklick und gibt die Position an Cursor
        """
        if self.game == "" or self.game.game_over:
            return
        x, y = event.x, event.y
        if (MARGIN < x < WIDTH - MARGIN and MARGIN < y < HEIGHT - MARGIN):
            self.canvas.focus_set()
            # holt die Reihe und Zeile von den x,y Koordinaten
            row, col = int((y - MARGIN) / SIDE), int((x - MARGIN) / SIDE)
            # Wenn die Zelle aktiviert ist, wird sie deaktiviert
            if (row, col) == (self.row, self.col):
                self.row, self.col = -1, -1
            elif self.game.start_puzzle[row][col] == 0:
                self.row, self.col = row, col
        else:
            self.row, self.col = -1, -1
        self.__draw_cursor()

    def __zaehleFest(self):
        ''' zählt die vorgegebenen Ziffern'''
        __anzFest = 81
        for i in range(9):
            __anzFest -= self.game.puzzle[i].count(0)
        return __anzFest

    def __istMoegl(self, zeile, spalte, testzahl):
        '''gibt True zurück, wenn Ziffer gesetzt werden darf'''
        return not testzahl in set(self.game.puzzle[zeile]) \
                and not testzahl in set([self.game.puzzle[row][spalte] for row in range(9)]) \
                and not testzahl in set([self.game.puzzle[row][col]
                        for row in range(zeile // 3 * 3, (zeile // 3 + 1) * 3)
                        for col in range(spalte // 3 * 3, (spalte // 3 + 1) * 3)])

    def __konsistent(self):
        '''prüft ob die festen Ziffern an der Position stehen dürfen'''
        ok=True
        for spalte in range(9):
            for zeile in range(9):
                testzahl = self.game.puzzle[zeile][spalte]  # speichere den Wert des betrachteten Feldes
                if(testzahl>0):
                    self.game.puzzle[zeile][spalte] = 0    # setze das Feld auf "leer" zur Prüfung)
                    ok &= self.__istMoegl(zeile, spalte, testzahl)
                    self.game.puzzle[zeile][spalte] = testzahl    # schreibe Zahl wieder ins Feld
        return ok

    def __bestimmeMoegl(self, zeile, spalte):
        ''' als Rückgabe Anzahl möglicher Ziffern und in moegl die möglichen Ziffern'''
        global moegl
        a = set(range(1, 10))
        # moegl als set
        self.zaehle += 1
        moegl = a - set(self.game.puzzle[zeile]) \
                - set([self.game.puzzle[row][spalte] for row in range(9)]) \
                - set([self.game.puzzle[row][col]
                     for row in range(zeile // 3 * 3, (zeile // 3 + 1) * 3)
                     for col in range(spalte // 3 * 3, (spalte // 3 + 1) * 3)])
        return len(moegl)

    def __loese(self, ebene):
        ''' durch einsetzen von möglichen Ziffern die Lösung suchen
            rekursive Aufrufe'''
        anzLoesungen = 0
        minAnzMoegl =10
        status=True
        __abbruch = False
        # finde Feld mit einer oder der kleinsten Anzahl Möglichkeiten
        for zeile in range(9):     
            for spalte in range(9):
                if self.game.puzzle[zeile][spalte]==0:
                    anzMoegl = self.__bestimmeMoegl(zeile,spalte)
                    if anzMoegl < minAnzMoegl:
                        spaltemin = spalte
                        zeilemin = zeile
                        minAnzMoegl = anzMoegl
                if minAnzMoegl == 1:
                    __abbruch = True
                    break
            if __abbruch:
                break
        if minAnzMoegl == 0: # geht nicht
            return False
        self.__bestimmeMoegl(zeilemin ,spaltemin) # Feld mit geringsten Möglichkeiten
        if ebene==80:   #fertig und letzte Zahl kann gesetzt werden
            self.game.puzzle[zeilemin][spaltemin] = moegl.pop() 
            self.game.loes_puzzle = deepcopy(self.game.puzzle)
            anzLoesungen += 1
            self.game.puzzle[zeilemin][spaltemin] = 0;
            if anzLoesungen < self.__maxLoesung+1:
                return True
            else:
                return False    # zu viele Lösungen
        if anzLoesungen < self.__maxLoesung+1:
            for i in moegl:
                self.game.puzzle[zeilemin][spaltemin] = i
                status &= self.__loese(ebene+1)     # rekursiverr Aufruf
                self.game.puzzle[zeilemin][spaltemin] = 0
        return status

    def __loesung(self, loesung_zeigen = True):
        ''' erster Aufruf von loese'''
        if not self.__geloest:
            __anzFest = self.__zaehleFest()
            if not self.__konsistent():
                print("nicht konsistent")
            elif __anzFest < 81:
                self.zaehle = 0
                t1 = time.time()
                self.__loese(__anzFest)
                t1 -= time.time()
                print("Anzahl Durchläufe = {0:5d}, und Zeit : {1:4.2f}".format(self.zaehle, t1))
            else:
                print("schon alle Zahlen gegeben")
            self.__geloest = True
        if loesung_zeigen:
            self.__draw_puzzle(True)

    def __eingabeOk(self):
        ''' Prüfung ob Ziffer ausser 0 bereits in Zeile, Spalte oder Quadrat vorhanden ist.
            Wenn Lösungsprüfung ein ist, wird auch richtige Ziffer im Feld geprüft'''
        if self.__pruefung.get():
            if not self.__geloest:
                self.__loesung(False)
            return self.eingabe != 0 and (self.eingabe == self.game.loes_puzzle[self.row][self.col])
        else:
            return self.eingabe != 0 and self.__istMoegl(self.row, self.col, self.eingabe)
    
    def __key_pressed(self, event):
        '''Auswertung einer Eingabe mit Prüfung'''
        if self.game == "" or self.game.game_over:
            return
        if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
            self.eingabe = int(event.char)
            if self.__eingabeOk():
                self.game.puzzle[self.row][self.col] = self.eingabe
                self.col, self.row = -1, -1
                self.__draw_puzzle()
                self.__draw_cursor()
                if self.game.check_win():
                    self.__draw_victory()
            else:
                if self.__pruefung.get():
                    messagebox.showinfo(message = 'Ziffer passt nicht zur Lösung')
                else:
                    messagebox.showinfo(message = 'Ziffer schon vorhanden')


    def __clear_answers(self):
        ''' Start Puzzel wieder herstellen '''
        if self.game != "":
            self.game.start(True)
            self.canvas.delete("victory")
            self.__draw_puzzle()

    def __andere_datei(self):
        ''' Auswahl einer anderen Datei oder Erstellung einer neuen Datei'''
        self.__geloest = False
        if self.neueEingabe:
            self.dateiname = "xxx.xxx"
        else:
            self.dateiname = openfile()
        self.a = self.dateiname.rsplit("/")
        self.bname = self.a[len(self.a)-1].split(".")
        with open(self.dateiname, 'r') as boards_file:
            self.parent.title("Sudoku  "+self.bname[0])
            self.game = SudokuGame(boards_file)
            self.game.start()
            self.canvas.delete("victory")
            self.__draw_puzzle()

    def __neue_datei(self):
        ''' Kennung für Erstellung einer neuen Datei'''
        self.neueEingabe = True
        self.__andere_datei()
        self.__draw_puzzle()

    def __speichern_datei(self):
        ''' Speichern des Spielstandes oder einer Neuerstellung'''
        if self.game != "" and not self.neueEingabe:
            with open(self.game.board_file.name +"u","w") as fobj:
                for i in range(9):
                    self.line = ""
                    for j in range(9):
                        self.line += str(
                            0 if self.game.puzzle[i][j] == self.game.start_puzzle[i][j]
                            else self.game.puzzle[i][j]
                            )
                    self.line += "\n"
                    fobj.write(self.line)
        elif self.neueEingabe:
            self.neueEingabe = False
            self.dateiname = savefile()
            with open(self.dateiname, "w") as fobj:
                for i in range(9):
                    self.line = ""
                    for j in range(9):
                        self.line += str(self.game.puzzle[i][j])
                    self.line += "\n"
                    fobj.write(self.line)
            self.__clear_answers()

class SudokuBoard(object):
    """
    Sudoku Board Puzzel aus Datei übernehmen
    """
    def __init__(self, board_file):
        self.board = self.__create_board(board_file)

    def __create_board(self, board_file):
        board = []
        for line in board_file:
            line = line.strip()
            board.append([])
            for c in line:
                board[-1].append(int(c))
        return board

class SudokuGame(object):
    """
    Ein Sudoku-Spiel, bei dem der Status des Bretts gespeichert und
    überprüft wird, ob das Puzzle vollständig ist.
    Vorbelegung des Spielfeldes, 
    """
    def __init__(self, board_file):
        self.board_file = board_file
        self.start_puzzle = SudokuBoard(board_file).board

    def start(self, clear = False):
        self.game_over = False
        self.clear = clear  #clear = puzzle ohne Eingaben einlesen
        self.puzzle = deepcopy(self.start_puzzle)
        self.loes_puzzle = deepcopy(self.start_puzzle)
        if not self.clear:  #Eingaben aus .sudokuu einlesen, wenn vorhanden
            save_file = self.board_file.name + "u"
            if os.path.isfile(save_file):
                with open(save_file, "r") as fobj:
                    self.save_puzzle = SudokuBoard(fobj).board
                    for i in range(9):
                        for j in range(9):
                            if self.puzzle[i][j] == 0:
                                self.puzzle[i][j] = self.save_puzzle[i][j]
                                self.loes_puzzle[i][j] = self.save_puzzle[i][j]


    def check_win(self):
        '''Prüfung ob alle Zahlen in Zeilen, Spalten u. Quadraten vorhanden sind'''
        for row in range(9):
            if not self.__check_row(row):
                return False
        for column in range(9):
            if not self.__check_column(column):
                return False
        for row in range(3):
            for column in range(3):
                if not self.__check_square(row, column):
                    return False
        self.game_over = True
        return True

    def __check_block(self, block):
        # Prüfung ob in der Menge (set) Block alle Ziffern 1-9 vorhanden sind
        return set(block) == set(range(1, 10))

    def __check_row(self, row):
        return self.__check_block(self.puzzle[row])

    def __check_column(self, column):
        return self.__check_block(
            [self.puzzle[row][column] for row in range(9)])

    def __check_square(self, row, column):
        return self.__check_block(
            [self.puzzle[r][c]
             for r in range(row * 3, (row + 1) * 3)
             for c in range(column * 3, (column + 1) * 3)])


if __name__ == '__main__':
    root = Tk()
    SudokuUI(root)
    root.mainloop()
