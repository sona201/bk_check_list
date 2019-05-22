function danger_filter(input_string){
    input_string=input_string.replace(/</g, '&lt;');

    input_string=input_string.replace(/>/g, '&gt;');

    input_string=input_string.replace(/'/g, "//'");
    return input_string;
}