#!/bin/bash

# Автоопределение интерфейса
INTERFACE=$(ip route | awk '/default/ {print $5}')

if [[ -z "$INTERFACE" ]]; then
    echo "Не удалось определить сетевой интерфейс"
    exit 1
fi

echo "Используется интерфейс: $INTERFACE"
echo

# IPv4 CIDR
CIDR_V4=$(ip -4 addr show "$INTERFACE" | awk '/inet / {print $2}')

# IPv6 link-local
CIDR_V6="fe80::/64"

echo "===== IPv4 scan ====="

if [[ -n "$CIDR_V4" ]]; then
    nmap -sn "$CIDR_V4" | \
    awk '
    /Nmap scan report for/ {
        if ($NF ~ /^\([0-9.]+\)$/) {
            # Формат: hostname (IP)
            ip=$NF
            gsub(/[()]/, "", ip)
            host=$5
            print ip " - " host
        } else {
            # Формат: IP без hostname
            ip=$NF
            print ip " - unknown"
        }
    }'
else
    echo "IPv4 адрес не найден"
fi

echo
echo "===== IPv6 scan ====="

nmap -6 -sn --interface "$INTERFACE" "$CIDR_V6" 2>/dev/null | \
awk '
/Nmap scan report for/ {
    print $NF
}'
