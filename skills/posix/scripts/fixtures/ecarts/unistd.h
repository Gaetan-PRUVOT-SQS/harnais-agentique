#ifndef UNISTD_H
# define UNISTD_H

long	write(int fd, const void *tampon, size_t taille);
int		getpid(void);
char	*strdup(const char *s);

#endif
