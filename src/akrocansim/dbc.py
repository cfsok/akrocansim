from pathlib import Path
import re

from . import signaltools


def _J1939_dbc(J1939DA: dict, PGNs_SPNs: dict) -> str:
    headers_1 = '''VERSION ""


NS_ : 
\tNS_DESC_
\tCM_
\tBA_DEF_
\tBA_
\tVAL_
\tCAT_DEF_
\tCAT_
\tFILTER
\tBA_DEF_DEF_
\tEV_DATA_
\tENVVAR_DATA_
\tSGTYPE_
\tSGTYPE_VAL_
\tBA_DEF_SGTYPE_
\tBA_SGTYPE_
\tSIG_TYPE_REF_
\tVAL_TABLE_
\tSIG_GROUP_
\tSIG_VALTYPE_
\tSIGTYPE_VALTYPE_
\tBO_TX_BU_
\tBA_DEF_REL_
\tBA_REL_
\tBA_DEF_DEF_REL_
\tBU_SG_REL_
\tBU_EV_REL_
\tBU_BO_REL_
\tSG_MUL_VAL_

BS_:

BU_:
'''
    BO_SG_ = '\n\n'
    headers_2 = '''

BA_DEF_ BO_  "J1939FdTpADS" INT 0 52;
BA_DEF_ BO_  "J1939FdTpADT" INT 0 255;
BA_DEF_ BO_  "J1939PgAppearanceOnBus" ENUM  "Default","CAN_Extended","CANFD_Extended";
BA_DEF_ BO_  "J1939CPgSendTimeout" INT -1 3600000;
BA_DEF_ BO_  "J1939CPgTOS" INT 0 7;
BA_DEF_ BO_  "J1939CPgTF" INT 0 7;
BA_DEF_ BU_  "J1939MultiPgSendTimeout" INT 0 3600000;
BA_DEF_ BU_  "J1939MultiPgSizeThreshold" INT 0 64;
BA_DEF_ BU_  "J1939MultiPgBroadcastType" ENUM  "FBFF","FEFF";
BA_DEF_  "DatabaseVersion" STRING ;
BA_DEF_ BO_  "FsJ1939UseCrcAndCounter" STRING ;
BA_DEF_ BO_  "FsJ1939NeedsSHM" ENUM  "No","Yes";
BA_DEF_ BO_  "FsJ1939Delay" INT 0 1000;
BA_DEF_ BO_  "TpJ1939VarDlc" ENUM  "No","Yes";
BA_DEF_ SG_  "SigType" ENUM  "Default","Range","RangeSigned","ASCII","Discrete","Control","ReferencePGN","DTC","StringDelimiter","StringLength","StringLengthControl","MessageCounter","MessageChecksum";
BA_DEF_ SG_  "GenSigILSupport" ENUM  "No","Yes";
BA_DEF_ SG_  "GenSigSendType" ENUM  "Cyclic","OnWrite","OnWriteWithRepetition","OnChange","OnChangeWithRepetition","IfActive","IfActiveWithRepetition","NoSigSendType";
BA_DEF_ BO_  "GenMsgFastOnStart" INT 0 100000;
BA_DEF_ SG_  "GenSigInactiveValue" INT 0 0;
BA_DEF_ BO_  "GenMsgCycleTimeFast" INT 0 3600000;
BA_DEF_ BO_  "GenMsgNrOfRepetition" INT 0 1000000;
BA_DEF_ SG_  "GenSigStartValue" INT 0 2147483647;
BA_DEF_ BO_  "GenMsgDelayTime" INT 0 1000;
BA_DEF_ BO_  "GenMsgILSupport" ENUM  "No","Yes";
BA_DEF_ BO_  "GenMsgStartDelayTime" INT 0 100000;
BA_DEF_ BU_  "NodeLayerModules" STRING ;
BA_DEF_ BU_  "ECU" STRING ;
BA_DEF_ BU_  "NmJ1939SystemInstance" INT 0 15;
BA_DEF_ BU_  "NmJ1939System" INT 0 127;
BA_DEF_ BU_  "NmJ1939ManufacturerCode" INT 0 2047;
BA_DEF_ BU_  "NmJ1939IndustryGroup" INT 0 7;
BA_DEF_ BU_  "NmJ1939IdentityNumber" INT 0 2097151;
BA_DEF_ BU_  "NmJ1939FunctionInstance" INT 0 7;
BA_DEF_ BU_  "NmJ1939Function" INT 0 255;
BA_DEF_ BU_  "NmJ1939ECUInstance" INT 0 7;
BA_DEF_ BU_  "NmJ1939AAC" INT 0 1;
BA_DEF_ BU_  "NmStationAddress" INT 0 255;
BA_DEF_ BO_  "GenMsgSendType" ENUM  "cyclic","NotUsed","NotUsed","NotUsed","NotUsed","NotUsed","NotUsed","IfActive","noMsgSendType";
BA_DEF_ BO_  "GenMsgRequestable" INT 0 1;
BA_DEF_ BO_  "GenMsgCycleTime" INT 0 3600000;
BA_DEF_ SG_  "SPN" INT 0 524287;
BA_DEF_  "DBName" STRING ;
BA_DEF_  "BusType" STRING ;
BA_DEF_  "ProtocolType" STRING ;
BA_DEF_ BO_  "VFrameFormat" ENUM  "StandardCAN","ExtendedCAN","reserved","J1939PG","reserved","reserved","reserved","reserved","reserved","reserved","reserved","reserved","reserved","reserved","StandardCAN_FD","ExtendedCAN_FD";
BA_DEF_DEF_  "J1939FdTpADS" 0;
BA_DEF_DEF_  "J1939FdTpADT" 0;
BA_DEF_DEF_  "J1939PgAppearanceOnBus" "Default";
BA_DEF_DEF_  "J1939CPgSendTimeout" -1;
BA_DEF_DEF_  "J1939CPgTOS" 2;
BA_DEF_DEF_  "J1939CPgTF" 0;
BA_DEF_DEF_  "J1939MultiPgSendTimeout" 2;
BA_DEF_DEF_  "J1939MultiPgSizeThreshold" 56;
BA_DEF_DEF_  "J1939MultiPgBroadcastType" "FBFF";
BA_DEF_DEF_  "DatabaseVersion" "";
BA_DEF_DEF_  "FsJ1939UseCrcAndCounter" "";
BA_DEF_DEF_  "FsJ1939NeedsSHM" "No";
BA_DEF_DEF_  "FsJ1939Delay" 0;
BA_DEF_DEF_  "TpJ1939VarDlc" "No";
BA_DEF_DEF_  "SigType" "Default";
BA_DEF_DEF_  "GenSigILSupport" "Yes";
BA_DEF_DEF_  "GenSigSendType" "NoSigSendType";
BA_DEF_DEF_  "GenMsgFastOnStart" 0;
BA_DEF_DEF_  "GenSigInactiveValue" 0;
BA_DEF_DEF_  "GenMsgCycleTimeFast" 0;
BA_DEF_DEF_  "GenMsgNrOfRepetition" 0;
BA_DEF_DEF_  "GenSigStartValue" 0;
BA_DEF_DEF_  "GenMsgDelayTime" 0;
BA_DEF_DEF_  "GenMsgILSupport" "Yes";
BA_DEF_DEF_  "GenMsgStartDelayTime" 0;
BA_DEF_DEF_  "NodeLayerModules" "";
BA_DEF_DEF_  "ECU" "";
BA_DEF_DEF_  "NmJ1939SystemInstance" 0;
BA_DEF_DEF_  "NmJ1939System" 0;
BA_DEF_DEF_  "NmJ1939ManufacturerCode" 0;
BA_DEF_DEF_  "NmJ1939IndustryGroup" 0;
BA_DEF_DEF_  "NmJ1939IdentityNumber" 0;
BA_DEF_DEF_  "NmJ1939FunctionInstance" 0;
BA_DEF_DEF_  "NmJ1939Function" 0;
BA_DEF_DEF_  "NmJ1939ECUInstance" 0;
BA_DEF_DEF_  "NmJ1939AAC" 0;
BA_DEF_DEF_  "NmStationAddress" 254;
BA_DEF_DEF_  "GenMsgSendType" "noMsgSendType";
BA_DEF_DEF_  "GenMsgRequestable" 1;
BA_DEF_DEF_  "GenMsgCycleTime" 0;
BA_DEF_DEF_  "SPN" 0;
BA_DEF_DEF_  "DBName" "";
BA_DEF_DEF_  "BusType" "CAN";
BA_DEF_DEF_  "ProtocolType" "J1939";
BA_DEF_DEF_  "VFrameFormat" "J1939PG";
BA_ "BusType" "CAN";
BA_ "DBName" "Tx_PGNs_SPNs";
'''
    VAL_TABLE_ = ''
    BA_messages = '\n\n'
    BA_signals = ''
    VAL_ = ''

    for pgn, spns in PGNs_SPNs.items():
        pgn_spec = J1939DA[pgn]
        frame_id = 1 << 31 | pgn_spec['Default Priority'] << 26 | pgn << 8 | 0
        pgn_name = re.sub('\W+', '_', f"{pgn_spec['Acronym']}_{pgn_spec['Parameter Group Label']}")
        pgn_name = '_' + pgn_name[:31] if pgn_name[0].isnumeric() else pgn_name[:32]

        BO_SG_ += f"BO_ {frame_id} {pgn_name}: {pgn_spec['PGN Data Length']} Vector__XXX\n"
        BA_messages += f'BA_ "VFrameFormat" BO_ {frame_id} 3;\n'

        for spn in spns:
            spn_spec = pgn_spec['SPNs'][spn]
            spn_name = re.sub('\W+', '_', f"SPN{spn}_{spn_spec['SPN Name']}")[:32]

            scale = spn_spec['scale'] if spn_spec['scale'] != 'ENUM' else 1

            BO_SG_ += (f" SG_ {spn_name} : "
                       f"{signaltools.start_bit(signal_spec=spn_spec)}|{spn_spec['length_bits']}@1+ "
                       f"({scale},{spn_spec['offset']}) [{spn_spec['min_value']}|{spn_spec['max_value']}] "
                       f'"{spn_spec["unit"]}" Vector__XXX\n')
            if spn_spec['scale'] not in ['ENUM']:
                BA_signals += (f'BA_ "GenSigStartValue" SG_ {frame_id} {spn_name} '
                               f'{signaltools.raw_min_value(signal_spec=spn_spec)};\n')
            elif spn_spec['scale'] == 'ENUM':
                value_label_strs = ''
                for value, label in spn_spec['discrete_values'].items():
                    value_label_strs = f'{value} "{label}" ' + value_label_strs

                VAL_TABLE_ += f'VAL_TABLE_ SPN_{spn}_value_labels {value_label_strs};\n'
                VAL_ += f'VAL_ {frame_id} {spn_name} {value_label_strs};'

        BO_SG_ += '\n'

    return f'{headers_1}{VAL_TABLE_}{BO_SG_}{headers_2}{BA_messages}{BA_signals}{VAL_}'


def dump_J1939_dbc(*, J1939DA: dict, PGNs_SPNs: dict, PGNs_SPNs_dbc: Path):
    dbc_content = _J1939_dbc(J1939DA, PGNs_SPNs)
    with PGNs_SPNs_dbc.open('w', encoding='utf-8') as f:
        f.write(dbc_content)
