import datetime
import random
numero_int = random.randint(10000, 99999)
def GenerateLOG(pathFile,msgText):
        try:
            dataAtual = datetime.datetime.now()
            msg = f'New LOG \n'
            msg += f'Data: {dataAtual.strftime('%Y-%m-%d')}\n'
            msg += f'Hora: {dataAtual.strftime('%H:%M')}\n'
            msg += f'\n'
            msg += f'Ticket:{numero_int}\n'
       
           
            msg += f'Mensagem: '
            msg += f'{msgText} \n'
            msg += f'\n---------------------------------------------------------\n\n'
 
            file_a = open(pathFile,'a')
            file_a.write(msg)
            file_a.close ()
       
            print('\n---Erro registado! Tente novamente.---\n')
        except:
            print('Erro na criação de Log.')
 