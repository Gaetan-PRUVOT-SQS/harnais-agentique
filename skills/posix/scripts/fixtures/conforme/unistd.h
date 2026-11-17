#ifndef UNISTD_H
# define UNISTD_H
# include <sys/types.h>

typedef struct s_rien
{
	int	champ;
}	t_rien;

ssize_t			write(int fd, const void *tampon, size_t taille);
pid_t			getpid(void);
int				pipe(int descripteurs[2]);
int				execve(const char *chemin, char *const argv[],
					char *const envp[]);
void			_exit(int code) __attribute__((noreturn));
unsigned int	sleep(unsigned int secondes);
int				ft_maison(void);

#endif
