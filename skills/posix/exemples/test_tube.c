#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "ecrire_tout.h"
#include "test_tube.h"

static unsigned char	g_donnees[TAILLE_TUBE];
static size_t			g_interrompus;

static void	ignorer_signal(int numero)
{
	(void)numero;
}

static ssize_t	write_compte(int fd, const void *tampon, size_t taille)
{
	ssize_t	r;

	r = write(fd, tampon, taille);
	if ((r < 0 && errno == EINTR) || (r >= 0 && (size_t)r < taille))
		g_interrompus++;
	return (r);
}

static int	armer_minuterie(timer_t *minuterie)
{
	struct sigaction	action;
	struct itimerspec	periode;

	memset(&action, 0, sizeof(action));
	action.sa_handler = ignorer_signal;
	sigemptyset(&action.sa_mask);
	if (sigaction(SIGALRM, &action, NULL) != 0
		|| timer_create(CLOCK_MONOTONIC, NULL, minuterie) != 0)
		return (-1);
	memset(&periode, 0, sizeof(periode));
	periode.it_interval.tv_nsec = 1000000;
	periode.it_value.tv_nsec = 1000000;
	return (timer_settime(*minuterie, 0, &periode, NULL));
}

static int	attendre(pid_t enfant, ssize_t ecrit)
{
	int	statut;

	while (waitpid(enfant, &statut, 0) < 0)
	{
		if (errno != EINTR)
			return (1);
	}
	if (ecrit != TAILLE_TUBE || !WIFEXITED(statut)
		|| WEXITSTATUS(statut) != 0 || g_interrompus == 0)
	{
		printf("[ko] tube lent : %zd octets, %zu interruptions\nFAIL\n",
			ecrit, g_interrompus);
		return (1);
	}
	printf("[ok] 4 Mio sur un tube lent, %zu ecritures interrompues ou "
		"partielles reprises\nPASS\n", g_interrompus);
	return (0);
}

int	main(void)
{
	int		tube[2];
	pid_t	enfant;
	timer_t	minuterie;
	ssize_t	ecrit;

	remplir(g_donnees, TAILLE_TUBE);
	if (pipe(tube) != 0)
		return (1);
	enfant = fork();
	if (enfant < 0)
		return (1);
	if (enfant == 0)
	{
		close(tube[1]);
		_exit(lire_lentement(tube[0]));
	}
	close(tube[0]);
	if (armer_minuterie(&minuterie) != 0)
		return (1);
	ecrit = ecrire_tout_avec(tube[1], g_donnees, TAILLE_TUBE, write_compte);
	timer_delete(minuterie);
	close(tube[1]);
	return (attendre(enfant, ecrit));
}
