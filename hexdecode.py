import time, os, glob
import toml
import logging
import argparse


#"""
# TODO
# 1. Destination log file rotation
# 2. Destination to Syslog server
#"""

def get_newest_source_file(source):
    #Get newest source file name
    latest_file = None
    list_of_files = glob.glob(source)
    logger.debug(f"Found source files: {list_of_files}")
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        logger.debug(f"Lasted source file: {latest_file}")
    return latest_file


#Data 
class Data:
    src_name_search = None
    dst_name_search = None
    src_name = None
    dst_name = None
    source_file = None
    destination_file = None
    source_rescan_count = 5


#Parser
parser = argparse.ArgumentParser()
parser.add_argument("-source","-s", metavar='FILE', help="hex lookup source file")
parser.add_argument("-config","-c", metavar='FILE', help="Optional: all parameters are stored in a config file instead")
parser.add_argument("-destination","-d", metavar='FILE', help="decoded hex output file")
parser.add_argument('--verbose', '--v', action='store_true', help="increase output verbosity")
parser.add_argument("--debug", "--d", action='store_true', help="debug output")
args = parser.parse_args()


#Logger
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger_stream_handler = logging.StreamHandler()
logger_formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s',"%Y-%m-%d %H:%M:%S")
logger_stream_handler.setFormatter(logger_formatter)
if args.debug:
    logger_stream_handler.setLevel(logging.DEBUG)
else:
    logger_stream_handler.setLevel(logging.INFO)
logger.addHandler(logger_stream_handler)


def main():
    #Check config/params
    if args.config:
        logger.debug(f"Loading config file: {args.config}")
        config = toml.load(args.config)
        Data.src_name_search = config["source"]
        Data.dst_name_search = config["destination"]
    else:
        if not args.source or not args.destination:
            logger.error("Source or Destination argument not suppled")
            quit()
        Data.src_name_search = args.source
        Data.dst_name_search = args.destination


    #Newest Files
    Data.src_name = get_newest_source_file(Data.src_name_search)
    Data.dst_name  = Data.dst_name_search
    if not Data.src_name:
        logger.error("Source File not found")
    elif not Data.dst_name:
        logger.error("Destination File not found")


    # Open files
    Data.source_file = open(Data.src_name,'r', encoding="utf8")


    #Find the size of the file and move to the end
    st_results = os.stat(Data.src_name)
    st_size = st_results[6]
    Data.source_file.seek(st_size)
    count = 0


    #Constantly check source file and decode hex to destination file
    while 1:
        where = Data.source_file.tell()
        line = Data.source_file.readline()
        if not line:
            time.sleep(1)
            count += 1
            Data.source_file.seek(where)
        else:
            count = 0
            if args.verbose:
                logger.info(line) 
            if line.startswith("0x"):
                logger.debug(line)
                dec = bytes.fromhex(line[2:]).decode('utf-8')
                with open(Data.dst_name, "a", encoding="utf8") as Data.destination_file:
                    Data.destination_file.write(dec)
                    Data.destination_file.write("\n")
                logger.debug(dec)

        #Check for a new sourcefile
        if count >= Data.source_rescan_count:
            count = 0
            new_file = get_newest_source_file(Data.src_name_search)
            if Data.src_name != new_file:
                old_file = Data.src_name
                logger.debug(f"New source file found: {new_file}")
                Data.src_name = new_file
                Data.source_file.close()
                Data.source_file = open(Data.src_name,'r', encoding="utf8")
                st_results = os.stat(Data.src_name)
                st_size = st_results[6]
                logger.debug(f"Source file changed. Old: {old_file}. New: {Data.src_name}")

if __name__ == "__main__":
    main()