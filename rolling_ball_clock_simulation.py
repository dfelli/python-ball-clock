import sys, time, json

# fills an array sequencially with the numbers 1 to count and returns it
def fill_sequencial_array(count):
    array = []
    for index in range(count):
        array.append(index + 1)
    return array

#checks and returns True if an array ordered sequencially
def sequence_is_ordered(array):
    for index in range(len(array)-1):
        if array[index] >=  array[index + 1]:
            return False
    return True

def print_sequences(sequences):
    # pick out the needed information and serialize it for json output
    json_sequences = {
        "Min": sequences["min"]["sequence"],
        "FiveMin": sequences["five_min"]["sequence"],
        "Hour": sequences["hour"]["sequence"],
        "Main": sequences["main"]["sequence"]
    }
    print(json.dumps(json_sequences))

#checks for the finished conditions for the two modes
def check_finished_state(sequences, params, main_bin_full):
    if params["mode"] == 2 and params["minutes_tracked"] >= params["minutes_to_simulate"]:
        print_sequences(sequences)
        time_diff = time.time() - params["start_time"]
        print("Completed in {:.0f} milliseconds ({:.3f} seconds)".format(int(time_diff*1000), time_diff))
        return True
    elif params["mode"] == 1 and main_bin_full and sequence_is_ordered(sequences["main"]["sequence"]):
        time_diff = time.time() - params["start_time"]
        print("{} balls cycle after {} days.".format(sequences["main"]["size"], int(params["minutes_tracked"]/60/24)))
        print("Completed in {:.0f} milliseconds ({:.3f} seconds)".format(int(time_diff*1000), time_diff))
        return True
    return False

# simulates one minute of time passing for a ball clock
# returns True if the conditions are met for the current running mode. Otherwise False is returned
def pass_one_minute(sequences, params):
    main_bin_full = False
    # increment the minutes of the simulation
    params["minutes_tracked"] = params["minutes_tracked"] + 1
    # the ball we are taking from the main sequence
    ball_to_move = sequences["main"]["sequence"][0]
    # remove the first ball of the main sequence
    sequences["main"]["sequence"] = sequences["main"]["sequence"][1:]
    # add the ball to the minute sequence
    sequences["min"]["sequence"].append(ball_to_move)

    # if the sequence is full, dump it and let its effects cascade
    if len(sequences["min"]["sequence"]) == sequences["min"]["size"]:
        main_bin_full = dump_the_sequence(sequences, "min", params)

    #check for finished conditions for the two modes
    return check_finished_state(sequences, params, main_bin_full)

# recursive function
# performs a ball clock dump when a holding pen is full
# the last added ball goes on to the next level, while the others
# return to the main pool in reverse order.
# returns True if all the balls are in the main sequence otherwise returns False
def dump_the_sequence(sequences, sequence_name, params):
    the_next_sequence = sequences[sequence_name]["next_sequence"]
    the_next_sequence_size = sequences[the_next_sequence]["size"]

    # get the last ball
    last_ball = sequences[sequence_name]["sequence"][-1]
    # remove that ball
    sequences[sequence_name]["sequence"] = sequences[sequence_name]["sequence"][:-1]
    # delay passing this ball to the next sequence (incase it is the 12th hours ball)
    # to handle the case where the other balls return to the main sequence before the 12th hour ball

    # return the rest of the balls to the main sequence in reverse order
    for index in range(len(sequences[sequence_name]["sequence"])):
        # take the last element in the sequence
        last_element = sequences[sequence_name]["sequence"][-1]
        # remove that ball
        sequences[sequence_name]["sequence"] = sequences[sequence_name]["sequence"][:-1]
        #append the last element to the main sequence
        sequences["main"]["sequence"].append(last_element)

    # pass the last ball to the next sequence
    sequences[the_next_sequence]["sequence"].append(last_ball)

    # when the main sequence is full we don't actually dump it
    # we return True indicating the main sequence is full
    if the_next_sequence is "main" and len(sequences["main"]["sequence"]) == the_next_sequence_size:
        return True

    # if the next sequence is full, dump it and let its effects cascade.
    if len(sequences[the_next_sequence]["sequence"]) == the_next_sequence_size:
        return dump_the_sequence(sequences, the_next_sequence, params)

    return False

# checks to see if input is a valid integer in between two values min and max
def validate_int_between(input, min, max):
    try:
        # we want to error on floats or anything with a decimal in it
        if '.' in str(input):
            raise Exception("non integer value given: {}: contains a dot or decimal. Exiting".format(input))
            sys.exit(1)
        # if we can't parse to an integer throw an error
        number = int(input)
    except:
        raise Exception("non integer value given: {}: {}. Exiting".format(input, type(input)))
        sys.exit(1)
    if number < min or number > max:
        raise Exception("Error the value must be between {} and {} inclusive. you provided {}. Exiting".format(min, max, number))
        sys.exit(1)
    return number

# parses user input to determine the number of balls to simulate and additionally the number of minutes to simulate
# 1 argument sets up mode 1. 2 arguments sets up mode 2
def parse_input(user_input):
    # remove any weird white space
    user_input = user_input.strip('\t\n\r')
    user_input = " ".join(user_input.split())

    # count the number of given parameters to determine the mode
    inputs = user_input.split()
    if len(inputs) == 1:
        #mode 1
        return validate_int_between(inputs[0], 27, 127), sys.maxint-1000, 1
    elif len(inputs) == 2:
        # mode 2
        return validate_int_between(inputs[0], 27, 127), validate_int_between(inputs[1], 0, sys.maxint-1000), 2
    else:
        print("too many inputs :{} expects 0 to 2. Exiting".format(inputs))
        sys.exit(1)

def handle_user_input(argv):
    # default to a high number of iterations to simulate
    minutes_to_simulate = sys.maxint
    num_balls = 27
    mode = 1

    #if the user doesn't provide any line arguments
    if len(argv) == 1:
        user_input = raw_input("""Enter in one of the following
            \tthe number of balls to simulate (mode 1)
            \tor the number of balls to simulate and the number of minutes to run the simulation (mode 2) separated by a space
            \thit the return key for easy mode (no input)\n""")

        # prompt for the users input one piece at a time
        if user_input == "":
            mode = raw_input("Enter the mode you would like to simulate 1 or 2: \n\t1)Cycle Days\n\t2)Clock State\n")
            mode = validate_int_between(mode, 1, 2)

            if mode == 1:
                # get the number of balls to simulate with
                num_balls = raw_input("Enter the number of balls to simulate: ")
                num_balls = validate_int_between(num_balls, 27, 127)
            elif mode == 2:
                # get the number of balls to simulate with
                num_balls = raw_input("Enter the number of balls to simulate: ")
                num_balls = validate_int_between(num_balls, 27, 127)
                # get the number of minutes to run the simulation
                minutes_to_simulate = raw_input("Enter the number of minutess to simulate: ")
                minutes_to_simulate = validate_int_between(minutes_to_simulate, 0, sys.maxint)
            else:
                print("invalid mode chosen: {}. Exiting".format(mode))
                sys.exit(1)
        else:
            # parse what they provided
            return parse_input(user_input)

    if len(argv) > 1:
        mode = 1
        num_balls = argv[1]
        num_balls = validate_int_between(num_balls, 27, 127)
    if len(argv) > 2:
        mode = 2
        minutes_to_simulate = argv[2]
        minutes_to_simulate = validate_int_between(minutes_to_simulate, 0, sys.maxint)
    if len(argv) > 3:
        print("too many arguments provided. please provide either the number of balls to simulate and optionally the number of iterations (minutes) to run. Exiting")
        sys.exit(1)
    return num_balls, minutes_to_simulate, mode

def main():
    #handle and validates what the user gives the program or prompts a user for the needed information
    num_balls, minutes_to_simulate, mode = handle_user_input(sys.argv)

    sequences = {
        "five_min": {"size": 12, "sequence":[], "next_sequence" : "hour"},
        "hour": {"size": 12, "sequence":[], "next_sequence" : "main"},
        "main": {"size": num_balls, "sequence":[], "next_sequence" : "min"},
        "min": {"size": 5, "sequence":[], "next_sequence" : "five_min"}
    }

    # fill up the main sequence with balls
    sequences["main"]["sequence"] = fill_sequencial_array(num_balls)

    finished = False

    params = {
        "minutes_to_simulate" : minutes_to_simulate,
        "minutes_tracked": 0,
        "mode": mode,
        "start_time": time.time()
    }
    # run the simulation until it finished
    while not finished:
        finished = pass_one_minute(sequences, params)

main()
