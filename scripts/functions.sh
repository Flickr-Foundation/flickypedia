print_info() {
    echo -e "\033[34m$1\033[0m"
}

print_error() {
    echo -e "\033[31m$1\033[0m" >&2
}

print_warning() {
    echo -e "\033[33m$1\033[0m"
}

print_success() {
    echo -e "\033[32m$1\033[0m"
}
