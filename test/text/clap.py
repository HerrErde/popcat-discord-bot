def clap(text):
    # Convert the string to lowercase to make it case-insensitive
    text = text.lower()
    # Initialize an empty string to store the result
    result = ""
    # Loop through each character in the string
    for i in range(len(text)):
        # If the character is not the first or last character in the string
        if i != 0:
            # Add :clap: before the character
            result += ":clap:"
        # Add the character to the result
        result += text[i]
    # Add :clap: at the end of the string
    result += ":clap:"
    return result


# Test the function with a sample string
input_string = "test"
output_string = insert_clap(input_string)
print(output_string)
