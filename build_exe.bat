pyinstaller src\akrocansim.py ^
            --onefile --noconsole ^
            --add-data="src/akrocansim/resources/akrocansim.ico:akrocansim/resources" ^
            --add-data="src/akrocansim/resources/akrocansim_logo_dark.png:akrocansim/resources" ^
            --icon src/akrocansim/resources/akrocansim.ico
