#include <string.h>
#include <unistd.h>

#define MESSAGE "[ok] init en mode utilisateur\n"

int	main(int argc, char **argv, char **envp)
{
	(void)argc;
	(void)argv;
	(void)envp;
	if (write(1, MESSAGE, strlen(MESSAGE)) < 0)
		return (1);
	return (0);
}
