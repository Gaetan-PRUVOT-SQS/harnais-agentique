#include <stdint.h>
#include <errno.h>
#include <unistd.h>
#include "appel_systeme.h"
#include "syscall.h"

long	resultat_systeme(long retour)
{
	if (retour < 0)
	{
		errno = (int)(-retour);
		return (-1);
	}
	return (retour);
}

ssize_t	write(int fd, const void *tampon, size_t taille)
{
	return ((ssize_t)resultat_systeme(appel_systeme(SYS_WRITE, fd,
				(long)(uintptr_t)tampon, (long)taille)));
}

pid_t	getpid(void)
{
	return ((pid_t)appel_systeme(SYS_GETPID, 0, 0, 0));
}

void	_exit(int code)
{
	while (1)
		appel_systeme(SYS_EXIT, code, 0, 0);
}
