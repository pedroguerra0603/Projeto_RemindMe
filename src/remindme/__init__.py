import logging

# Quem executa a aplicação configura o log; sem isso, o registro de erro (RNF-21) não aparece na saída.
logging.getLogger("remindme").addHandler(logging.NullHandler())
