import sys, re

#Lee cada linea del archivo, también reporta el estado de la linea actual 
class Parser():
    igual = '='
    puntoycoma = ';'

    #Constructor de la clase, carga el archivo,  e inicializa las variables del 
    #comando_actual, siguiente_linea, hasMoreLines
    def __init__(self, inputFile):
        self.inputFile = open(inputFile, 'r') #Abre el archivo en modo lectura
        self.comando_actual = None
        self.siguiente_linea = None
        self.hasMoreLines = True

    #Esta método es el responsable de volver a inicial la lectura del archivo desde el inicio
    #(seek(0))
    def reset(self):
        self.inputFile.seek(0)
        self.comando_actual = None
        self.siguiente_linea = None
        self.hasMoreLines = True

    # En este metoodo se retorna el string que hay antes de un '=' para ponerlo
    # que es el dest
    def destStr(self):
        if self.comando_actual.find(self.igual) != -1:
            return self.comando_actual.split(self.igual)[0]

    # cuando hay un punto y coma en la linea devuelve lo que hay 
    # después del punto y coma, esto es para el jump
    def jumpStr(self):
        if self.comando_actual.find(self.puntoycoma) != -1:
            return self.comando_actual.split(self.puntoycoma)[1]

    # si hay un igual devuelve lo que hay después del igual, esto es para el comp
    # pero si en cambio hay un punto y coma devuelve lo que está antes del punto y coma
    def compStr(self):
        if self.comando_actual.find(self.igual) != -1:
            return self.comando_actual.split(self.igual)[1]
        elif self.comando_actual.find(self.puntoycoma) != -1:
            return self.comando_actual.split(self.puntoycoma)[0]

    # Este metodo devuelve de la linea actual el simbolo, ya sea un string o ún numero
    # Ejemplo de @i devolvería i, de (LOOP) devolvería LOOP
    def symbol(self):
        return ''.join(c for c in self.comando_actual if c not in '()@/')

    def advance(self):
        # Este método pasa a la siguiente linea en el archivo

        # pregunta por la linea actual, si es None, quiere decir que es la primera 
        # vez que empieza a leer, entonces lee la siguiente linea
        if self.comando_actual == None:
            self.comando_actual = self.inputFile.readline()
        else:
            self.comando_actual = self.siguiente_linea

        # aquí llama al metodo cleanLine para quitar los comentarios
        # y lineas en blanco
        self.comando_actual = self.cleanLine(self.comando_actual)

        self.siguiente_linea = self.inputFile.readline()
        # sí la siguiente linea es '', quiere decir que no hay más lineas por leer
        # las lineas vacias son '\n'
        if self.siguiente_linea == '':
            self.hasMoreLines = False

        self.findCommandType()

    def cleanLine(self, line):
        line = line.strip()
        # quita los comentarios
        line = line.split('//')[0]
        line = line.strip(' ')
        return line

    def findCommandType(self):
        # define si el comando actual es una instrucción, dirección, etiqueta o un calculo
        if self.comando_actual == '':
            self.actualCommandType = 'not_instruction'
        elif self.comando_actual[0] == '@':
            self.actualCommandType = 'address'
        elif self.comando_actual[0] == '(':
            self.actualCommandType = 'label'
        else:
            self.actualCommandType = 'computation'

class Decoder():
    destBits = {
        None : '000',
        'M'  : '001',
        'D'  : '010',
        'MD' : '011',
        'A'  : '100',
        'AM' : '101',
        'AD' : '110',
        'AMD': '111'
    }

    compBits = {
        None : '',
        '0'  : '0101010',
        '1'  : '0111111',
        '-1' : '0111010',
        'D'  : '0001100',
        'A'  : '0110000',
        'M'  : '1110000',
        '!D' : '0001101',
        '!A' : '0110001',
        '!M' : '1110001',
        '-D' : '0001111',
        '-A' : '0110011',
        '-M' : '1110011',
        'D+1': '0011111',
        'A+1': '0110111',
        'M+1': '1110111',
        'D-1': '0001110',
        'A-1': '0110010',
        'M-1': '1110010',
        'D+A': '0000010',
        'D+M': '1000010',
        'D-A': '0010011',
        'D-M': '1010011',
        'A-D': '0000111',
        'M-D': '1000111',
        'D&A': '0000000',
        'D&M': '1000000',
        'D|A': '0010101',
        'D|M': '1010101'
    }

    jumpToBits = {
        None : '000',
        'JGT': '001',
        'JEQ': '010',
        'JGE': '011',
        'JLT': '100',
        'JNE': '101',
        'JLE': '110',
        'JMP': '111'
    }

    instructionCInitBits = '111'

    # Recibe un numero decimal y retorn un binario en String
    @classmethod
    def decimalToBinaryString(cls, num):
        return '{0:016b}'.format(num)


#Esta clase contiene los simbolos reservados del lenguaje, y cuando se hace el Parse
#de los labels se agregan a este diccionario de simbolos
class symbolDictionary():
    reservedSymbols = {
        'SP'  : 0,
        'LCL' : 1,
        'ARG' : 2,
        'THIS': 3,
        'THAT': 4,
        'R0'  : 0,
        'R1'  : 1,
        'R2'  : 2,
        'R3'  : 3,
        'R4'  : 4,
        'R5'  : 5,
        'R6'  : 6,
        'R7'  : 7,
        'R8'  : 8,
        'R9'  : 9,
        'R10' : 10,
        'R11' : 11,
        'R12' : 12,
        'R13' : 13,
        'R14' : 14,
        'R15' : 15,
        'SCREEN': 16384,
        'KBD'   : 24576
    }

    #Constructor de la clase, define la diguiente dirección de memoria
    # para ser utilizada por algún otro simbolo que no esté definido en 
    # el diccionario de simbolos
    def __init__(self):
        self.symbols = self.reservedSymbols
        self.nextAllowedAddress = 16

    # Cuando se reconoce una nueva etiqueta, se agrega su simbolo, con la dirección de la 
    # instrucción siguiente, esto se pasa en el argumento address
    def addEntry(self, symbol, address=None):
        if address:
            self.symbols[symbol] = address
        else:
            self.symbols[symbol] = self.nextAllowedAddress
            self.nextAllowedAddress += 1

        return self.getAdrress(symbol)

    # Este es un metodo booleano, pregunta si un simbolo está contenido
    # dentro del diccionario
    def contains(self, symbol):
        return symbol in self.symbols

    #Obtiene la dirección de un simbolo definido en el diccionario
    def getAdrress(self, symbol):
        return self.symbols[symbol]

#Esta es la clase principal
class main():
    # Constructor del main, instancia la clase Parser en el objeto parse
    # e instancia la clase symbolDictionary en el objeto symbolTable
    def __init__(self, inputFile):
        self.parser = Parser(inputFile)
        self.symbolTable = symbolDictionary()

    # Este es el metodo que llama a parseLabels, luego resetea el archivo 
    # en la posición 0 y finalmente traduce el archivo en codigo binario
    def run(self):
        self.parseLabels()
        self.parser.reset()
        self.translate()

    # Lo primero es analizar en busca de etiquetas, para definir la dirección de
    # la instrucción, como simbolo
    def parseLabels(self):
        num_instructions_so_far = 0

        while self.parser.hasMoreLines:
            self.parser.advance()

            if self.parser.actualCommandType == 'not_instruction':
                continue
            elif self.parser.actualCommandType == 'label':
                self.symbolTable.addEntry(symbol=self.parser.symbol(), address=num_instructions_so_far)
            else:
                num_instructions_so_far += 1

    #Este metodo es el encargado de una vez definidos todos los simbolos,
    #convertir las diferentes instrucciones en codigo binario y envíarlos al archivo .hack
    def translate(self):
        #Obtiene el nombre que le va a dar al archivo, tiene el mismo nombre
        # del .asm ingresado
        hackFileName = self.parser.inputFile.name.split('.')[0] + '.hack'
        # instancia el objeto hackFile con el archivo hackFileName en modo escrituta,
        # si no existe, lo crea
        hackFile = open(hackFileName, 'w+')

        # Obtiene el patrón de todas las letrs del abecedario, mayusculas y minusculas, a través
        # de una expresión regular
        lettersPattern = re.compile('[a-zA-Z]+')

        #Este ciclo se encarga de leer el archivo hasta que no tenga más lineas 
        while self.parser.hasMoreLines:
            self.parser.advance()
            code = ''

            # Sí es una instrucción de dirección @...
            if self.parser.actualCommandType == 'address':
                symbol = self.parser.symbol()
                #Obtiene el simbolo y verifica sí es un numero de dirección especifico
                # ó un simbolo ya definido en el diccionario de simbolos ó un simbolo que va 
                # a ser agregado a partir de la siguiente dirección permitida 16.....
                not_number = lettersPattern.match(symbol)

                if not_number:
                    if self.symbolTable.contains(symbol):
                        register_number = self.symbolTable.getAdrress(symbol)
                    else:
                        register_number = self.symbolTable.addEntry(symbol)
                else:
                    register_number = int(symbol)

                code = Decoder.decimalToBinaryString(register_number)
            #Sí es un calculo, busca los patrones del Decoder
            elif self.parser.actualCommandType == 'computation':
                # Éstos serán los 3 primeros bits
                initBits = Decoder.instructionCInitBits
                # Obtiene los siguientes bits; comp, dest y jump a partir de Decoder
                compStr = self.parser.compStr()
                compBits = Decoder.compBits[compStr]
                destStr = self.parser.destStr()
                destBits = Decoder.destBits[destStr]
                jumpStr = self.parser.jumpStr()
                jumpBits = Decoder.jumpToBits[jumpStr]

                code = initBits + compBits + destBits + jumpBits

            if len(code) > 0:
                hackFile.write(code + '\n')

        hackFile.close()

print ("Number of arguments: ", len(sys.argv))
print ("The arguments are: " , str(sys.argv))
assemblerInputFile = sys.argv[1]
assembler = main(assemblerInputFile)
assembler.run()
