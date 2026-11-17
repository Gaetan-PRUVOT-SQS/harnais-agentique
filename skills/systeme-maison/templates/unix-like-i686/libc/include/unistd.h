#ifndef UNISTD_H
# define UNISTD_H
# include <sys/types.h>

ssize_t	write(int fd, const void *tampon, size_t taille);
pid_t	getpid(void);
void	_exit(int code) __attribute__((noreturn));

#endif
