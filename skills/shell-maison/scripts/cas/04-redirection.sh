#!/bin/sh
{ echo sortie; echo erreur >&2; } 2>&1 | cat
