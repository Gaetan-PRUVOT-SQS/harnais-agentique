#include <stddef.h>
#include "errno.h"

extern const char	*g_errno_messages[];

int	l_echoue(int code)
{
	errno = code;
	return (-1);
}

const char	*l_strerror(int code)
{
	if (code <= 0 || code > ENOSYS || g_errno_messages[code] == NULL)
		return ("Erreur inconnue");
	return (g_errno_messages[code]);
}
