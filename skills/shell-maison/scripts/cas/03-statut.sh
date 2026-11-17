#!/bin/sh
false
echo "$?"
true && echo ok || echo ko
